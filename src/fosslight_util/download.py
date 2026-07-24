#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import sys
import requests
import tarfile
import zipfile
import logging
import argparse
import shutil
from git import Git
import bz2
import contextlib
from datetime import datetime
from pathlib import Path
from fosslight_util._get_downloadable_url import get_downloadable_url
from fosslight_util.help import print_help_msg_download
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
import signal
import time
import threading
import platform
import subprocess
import re
from typing import List, Optional, Tuple
import urllib.parse
import json

logger = logging.getLogger(constant.LOGGER_NAME)
compression_extension = {
    ".tar.bz2",
    ".tar.gz",
    ".tar.xz",
    ".tgz",
    ".tar",
    ".zip",
    ".jar",
    ".bz2",
    ".whl",
    ".src.rpm",
    ".rpm",
}
prefix_refs = ["refs/remotes/origin/", "refs/tags/"]
SIGNAL_TIMEOUT = 600
SIZE_CHECK_INTERVAL_SECONDS = 10
_BYTES_PER_GB = 1024 ** 3

# Some mirrors (e.g. mirrors.ustc.edu.cn) return 403 for python-requests' default
# User-Agent, or 200 with a small text/html interstitial. Start with a curl-style UA
# (widely accepted for file downloads), then browser, then default requests as fallback.
_HTTP_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_HTTP_CURL_LIKE_USER_AGENT = "curl/8.7.1"

# Substrings from actual size-limit error messages only
# (git clone size guard / HTTP-wget size checks).
_SIZE_LIMIT_BLOCK_MARKERS = (
    "temporary directory size exceeded",  # Download aborted: temporary directory size exceeded limit ...
    "Download aborted due to size limit",
)


class _HtmlWhenBinaryExpected(Exception):
    """Server returned HTML for a URL that should be a binary archive; try another client."""


class SizeLimitExceeded(Exception):
    """Raised when an HTTP/wget download exceeds ``size_limit_gb``."""


def _url_looks_like_binary_archive(url: str) -> bool:
    path = urllib.parse.urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in compression_extension)


def _download_http_header_attempts():
    return [
        {"User-Agent": _HTTP_CURL_LIKE_USER_AGENT, "Accept": "*/*"},
        {"User-Agent": _HTTP_BROWSER_USER_AGENT},
        None,
    ]


class Alarm(threading.Thread):
    def __init__(self, timeout):
        threading.Thread.__init__(self)
        self.timeout = timeout
        self.setDaemon(True)

    def run(self):
        time.sleep(self.timeout)
        logger.error("download timeout! (%d sec)", SIGNAL_TIMEOUT)
        os._exit(1)


class TimeOutException(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code


def alarm_handler(signum, frame):
    logger.warning("download timeout! (%d sec)", SIGNAL_TIMEOUT)
    raise TimeOutException(f'Timeout ({SIGNAL_TIMEOUT} sec)', 1)


def is_downloadable(url):
    """Probe URL; retry with alternate User-Agents on 403 or HTML body for archive URLs."""
    attempts = _download_http_header_attempts()
    last_i = len(attempts) - 1
    for i, headers in enumerate(attempts):
        try:
            with requests.get(
                url, stream=True, allow_redirects=True, timeout=10, headers=headers
            ) as r:
                if r.status_code == 403 and i < last_i:
                    continue
                if r.status_code >= 400:
                    return False
                content_type = r.headers.get('content-type', '').lower()
                if 'text/html' in content_type:
                    if _url_looks_like_binary_archive(url) and i < last_i:
                        continue
                    logger.warning(
                        f"Content-Type is text/html, not a downloadable link: {url}"
                    )
                    return False
                return True
        except Exception as e:
            if i < last_i:
                logger.info(
                    "is_downloadable: %s; retrying with alternate User-Agent", e
                )
                continue
            logger.warning(f"is_downloadable - failed: {e}")
            return False
    return False


def change_src_link_to_https(src_link):
    src_link = src_link.replace("git://", "https://")
    if src_link.endswith(".git"):
        src_link = src_link.replace('.git', '')
    return src_link


def change_ssh_link_to_https(src_link):
    src_link = src_link.replace("git@github.com:", "https://github.com/")
    return src_link


def _is_size_limit_block_message(msg: str) -> bool:
    if not msg:
        return False
    return any(marker in msg for marker in _SIZE_LIMIT_BLOCK_MARKERS)


def parse_src_link(src_link):
    src_info = {"url": src_link}
    src_link_changed = ""
    if src_link.startswith("git://") or src_link.startswith("git@") \
            or src_link.startswith("https://") or src_link.startswith("http://"):
        src_link_split = src_link.split(';')
        if src_link.startswith("git://github.com/"):
            src_link_changed = change_src_link_to_https(src_link_split[0])
        elif src_link.startswith("git@github.com:"):
            src_link_changed = src_link_split[0]
        else:
            if "rubygems.org" in src_link:
                src_info["rubygems"] = True
            src_link_changed = src_link_split[0]

        branch_info = [s for s in src_link_split if s.startswith('branch')]
        tag_info = [s for s in src_link_split if s.startswith('tag')]

        src_info["url"] = src_link_changed
        src_info["branch"] = branch_info
        src_info["tag"] = tag_info
    return src_info


def cli_download_and_extract(link: str, target_dir: str, log_dir: str, checkout_to: str = "",
                             compressed_only: bool = False, ssh_key: str = "",
                             id: str = "", git_token: str = "",
                             called_cli: bool = True,
                             output: bool = False,
                             size_limit_gb: Optional[float] = None
                             ) -> Tuple[bool, str, str, str, str]:
    global logger

    success = True
    msg = ""
    msg_wget = ""
    oss_name = ""
    oss_version = ""
    downloaded_link = ""
    size_limit_blocked = False
    log_file_name = "fosslight_download_" + \
        datetime.now().strftime('%Y%m%d_%H-%M-%S')+".txt"
    logger, log_item = init_log(os.path.join(log_dir, log_file_name))
    link = link.strip()
    is_rubygems = False

    try:
        if not link:
            success = False
            msg = "Need a link to download."
        elif os.path.isfile(target_dir):
            success = False
            msg = f"The target directory exists as a file.: {target_dir}"
        elif os.path.exists(link) or os.path.isdir(link) or os.path.isfile(link):
            success = False
            msg = f"You cannot enter a path instead of a link.: {link}"
        else:
            src_info = parse_src_link(link)
            link = src_info.get("url", "")
            tag = ''.join(src_info.get("tag",  "")).split('=')[-1]
            branch = ''.join(src_info.get("branch", "")).split('=')[-1]
            is_rubygems = src_info.get("rubygems", False)

            # General download (git clone, wget)
            success_git, msg, oss_name, oss_version, _ = download_git_clone(
                link, target_dir, checkout_to, tag, branch,
                ssh_key, id, git_token, called_cli, size_limit_gb=size_limit_gb)
            link = change_ssh_link_to_https(link)
            if success_git:
                downloaded_link = link
                success = True
            size_limit_blocked = _is_size_limit_block_message(msg)
            if size_limit_blocked:
                success = False
            elif (not is_rubygems) and (not success_git):
                if os.path.isfile(target_dir):
                    shutil.rmtree(target_dir)

                success, downloaded_file, msg_wget, oss_name, oss_version, resolved_link = download_wget(
                    link, target_dir, compressed_only, checkout_to,
                    size_limit_gb=size_limit_gb,
                )
                if _is_size_limit_block_message(msg_wget):
                    size_limit_blocked = True
                    success = False
                    msg = msg_wget
                elif success and downloaded_file:
                    success = extract_compressed_file(downloaded_file, target_dir, True, compressed_only)
                    if success:
                        downloaded_link = resolved_link
            # Download from rubygems.org
            elif is_rubygems and shutil.which("gem"):
                success = gem_download(link, target_dir, checkout_to)
                if success:
                    downloaded_link = link
        if size_limit_blocked:
            # Keep a clear size-limit message for callers/UI (do not wrap as git/wget fail)
            pass
        elif msg:
            msg = f'git fail: {msg}'
            if is_rubygems:
                msg = f'gem download: {success}'
            else:
                if msg_wget:
                    msg = f'{msg}, wget fail: {msg_wget}'
                else:
                    msg = f'{msg}, wget success'
        elif msg_wget:
            msg = f'wget fail: {msg_wget}'

    except Exception as error:
        success = False
        msg = str(error)

    clarified_version = clarified_version_from_oss_version(oss_version)
    output_link = downloaded_link if success else ""
    output_result = {
        "success": success,
        "message": msg,
        "link": output_link,
        "oss_name": oss_name,
        "oss_version": oss_version,
        "clarified_version": clarified_version,
    }
    if output:
        output_json = os.path.join(log_dir, "fosslight_download_output.json")
        with open(output_json, 'w') as f:
            json.dump(output_result, f, indent=4)

    logger.info(f"\n* FOSSLight Downloader - Result: {output_result})")
    return success, msg, oss_name, oss_version, clarified_version


def get_ref_to_checkout(checkout_to, ref_list):
    ref_to_checkout = checkout_to
    try:
        checkout_to = checkout_to.strip()
        if checkout_to in ref_list:
            return checkout_to

        for prefix in prefix_refs:
            ref_to_checkout = prefix+checkout_to
            if ref_to_checkout in ref_list:
                return ref_to_checkout

        ref_to_checkout = next(
            x for x in ref_list if x.endswith(checkout_to))
    except Exception as error:
        logger.warning(f"git find ref - failed: {error}")
    return ref_to_checkout


def get_remote_refs(git_url: str):
    if not git_url:
        return {"tags": [], "branches": []}
    tags = []
    branches = []
    try:
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_ASKPASS"] = "echo"
        env["GIT_CREDENTIAL_HELPER"] = ""
        if "GIT_SSH_COMMAND" not in env:
            env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=no"
        else:
            env["GIT_SSH_COMMAND"] = env["GIT_SSH_COMMAND"] + " -o BatchMode=yes"
        cp = subprocess.run(
            ["git", "-c", "credential.helper=", "-c", "credential.helper=!",
             "ls-remote", "--tags", "--heads", git_url],
            env=env, capture_output=True, text=True, timeout=30,
            stdin=subprocess.DEVNULL)
        if cp.returncode == 0:
            for line in cp.stdout.splitlines():
                parts = line.split('\t')
                if len(parts) != 2:
                    continue
                ref = parts[1]
                if ref.startswith('refs/tags/'):
                    tags.append(ref[len('refs/tags/'):])
                elif ref.startswith('refs/heads/'):
                    branches.append(ref[len('refs/heads/'):])
    except Exception as e:
        logger.debug(f"get_remote_refs - failed: {e}")
    return {"tags": tags, "branches": branches}


_BASE_SEMVER_FOR_CHECKOUT = re.compile(
    r'^(?:v\.? ?)?(\d+)\.(\d+)(?:\.(\d+))?'
    r'(?:(?:-[0-9A-Za-z.-]+)|(?:\.[A-Za-z][0-9A-Za-z.-]*))?'
    r'(?:\+[0-9A-Za-z.-]+)?$',
    re.IGNORECASE,
)
_SEMVER_IN_REF = re.compile(
    r'(?:^v\.? ?|[-_]v\.? ?|[-_])'
    r'(\d+)\.(\d+)\.(\d+)'
    r'(?:(?:-[0-9A-Za-z.-]+)|(?:\.[A-Za-z][0-9A-Za-z.-]*))?'
    r'(?:\+[0-9A-Za-z.-]+)?'
    r'(?=[-_]|$)',
    re.IGNORECASE,
)
_SEMVER_AT_REF_START = re.compile(
    r'^(\d+)\.(\d+)\.(\d+)'
    r'(?:(?:-[0-9A-Za-z.-]+)|(?:\.[A-Za-z][0-9A-Za-z.-]*))?'
    r'(?:\+[0-9A-Za-z.-]+)?'
    r'(?=[-_]|$)',
    re.IGNORECASE,
)
_SEMVER_DOT_QUALIFIER_IN_STR = re.compile(
    r'(\d+)\.(\d+)\.(\d+)\.[A-Za-z][0-9A-Za-z.-]*',
    re.IGNORECASE,
)
_CLARIFIED_MAJOR_ONLY_FULL = re.compile(r'^(?:v\.? ?)?(\d+)$', re.IGNORECASE)
# Maven / OSGi style: 1.1.7.7 (more than three numeric segments; not strict semver)
_PURE_DOT_NUMERIC_VERSION = re.compile(r'^\d+(\.\d+)+$')
# Two-part x.y not followed by .digit (avoids taking "1.2" from "1.2.3")
_CLARIFIED_TWO_IN_STR = re.compile(r'(\d+)\.(\d+)(?!\.\d)')
_CLARIFIED_MAJOR_IN_STR = re.compile(
    r'(?:^|[-_/])(?:v\.? ?)?(\d+)(?=[^.\d]|$)', re.IGNORECASE
)
# Trailing tarball version: ...-1.2.3 or ...-4.19.1.1-release (GNU / GitHub archive names)
_ARCHIVE_VERSION_TAIL = re.compile(
    r'-((?:\d+\.)+\d+(?:-[0-9A-Za-z][0-9A-Za-z.-]*)?)$',
    re.IGNORECASE,
)
# crates.io: API download URL ends with .../name/VERSION/download (basename must not be used as version)
_CRATES_IO_API_VERSION = re.compile(
    r'/api/v1/crates/[^/]+/([^/]+)/download/?$',
    re.IGNORECASE,
)
# crates.io: .../crates/CRATE_NAME/VERSION
_CRATES_IO_WEB_VERSION = re.compile(
    r'/crates/[^/]+/([^/?#]+)/?(?:$|[?#])',
    re.IGNORECASE,
)
_MAVEN_CLASSIFIER_SUFFIX_VERSION = re.compile(
    r'^(\d+(?:\.\d+){1,3})-(?:sources?|src|javadoc)(?:[-.].*)?$',
    re.IGNORECASE,
)


def _strip_debian_epoch_prefix(s: str) -> str:
    if re.match(r'^\d+:', s):
        return s.split(':', 1)[1]
    return s


def clarified_version_from_oss_version(oss_version: str) -> str:
    """Extract major, major.minor, or major.minor.patch from oss_version/ref string."""
    s = (oss_version or "").strip()
    if not s:
        return ""
    core = _strip_leading_v_prefix(_strip_debian_epoch_prefix(s))
    if _PURE_DOT_NUMERIC_VERSION.match(core):
        return core
    m = _BASE_SEMVER_FOR_CHECKOUT.match(core)
    if m:
        if m.group(3):
            return f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
        return f"{m.group(1)}.{m.group(2)}"
    m = _CLARIFIED_MAJOR_ONLY_FULL.match(core)
    if m:
        return m.group(1)
    m = _SEMVER_IN_REF.search(core) or _SEMVER_AT_REF_START.match(core)
    if m:
        return f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
    m = _SEMVER_DOT_QUALIFIER_IN_STR.search(core)
    if m:
        return f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
    m = _CLARIFIED_TWO_IN_STR.search(core)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    m = _CLARIFIED_MAJOR_IN_STR.search(core)
    if m:
        return m.group(1)
    return ""


def _strip_known_archive_suffixes(filename: str) -> str:
    """Remove trailing compression/archive extensions (e.g. bison-3.8.2.tar.xz -> bison-3.8.2)."""
    name = filename
    while name:
        low = name.lower()
        stripped = False
        for ext in sorted(compression_extension, key=len, reverse=True):
            if low.endswith(ext):
                name = name[: -len(ext)]
                stripped = True
                break
        if not stripped:
            break
    return name


def _version_string_from_archive_stem(stem: str) -> str:
    """Take trailing version segment from name-version stems (e.g. bison-3.8.2 -> 3.8.2)."""
    if not stem:
        return ""
    m = _ARCHIVE_VERSION_TAIL.search(stem)
    if m:
        version = m.group(1)
        # Maven source/javadoc artifact names can include classifier suffixes
        # (e.g. 2.12-sources). Keep the base numeric version for checkout hint.
        classifier = _MAVEN_CLASSIFIER_SUFFIX_VERSION.match(version)
        if classifier:
            return classifier.group(1)
        return version
    return stem


def _oss_version_hint_from_wget_link(link: str, downloaded_file: str) -> str:
    """Version string from last URL path segment or saved filename for clarified_version."""
    if link:
        path = urllib.parse.urlparse(link).path or ""
        m = _CRATES_IO_API_VERSION.search(path)
        if m:
            return m.group(1)
        m = _CRATES_IO_WEB_VERSION.search(path)
        if m:
            return m.group(1)

    for src in (link, downloaded_file):
        if not src:
            continue
        if isinstance(src, str) and src.startswith(("http://", "https://")):
            path = urllib.parse.urlparse(src).path
            base = os.path.basename(path.rstrip("/"))
        else:
            base = os.path.basename(str(src))
        if not base:
            continue
        stem = _strip_known_archive_suffixes(base)
        if not stem or stem.lower() == "download":
            continue
        return _version_string_from_archive_stem(stem)
    return ""


def _strip_leading_v_prefix(s: str) -> str:
    return re.sub(r'^(?:v\.? ?)?', '', s.strip(), flags=re.IGNORECASE)


def _repo_name_from_git_url(git_url: str) -> str:
    """Extract repository name from common git HTTPS/SSH URLs."""
    if not git_url:
        return ""
    url = git_url.strip().rstrip('/')
    if url.endswith('.git'):
        url = url[:-4]
    m = re.match(r'git@[^:]+:[^/]+/([^/@?#]+)$', url)
    if m:
        return m.group(1)
    path = urllib.parse.urlparse(url).path.strip('/')
    if path:
        segments = path.split('/')
        if len(segments) >= 2:
            return segments[-1]
    return ""


def _repo_prefixed_version_refs(repo_name: str, base: str) -> List[str]:
    """Build {repo}-v{version} style tag candidates from checkout hint."""
    if not repo_name or not base:
        return []
    base = base.strip()
    core = _strip_leading_v_prefix(base)
    if not core:
        return []
    repo = repo_name.strip()
    candidates = [
        f"{repo}-v{core}",
        f"{repo}-v.{core}",
        f"{repo}_{core}",
        f"{repo}-{core}",
    ]
    seen = set()
    result = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            result.append(candidate)
    return result


def _match_exact_or_v_prefix_ref(base: str, ref_set: set) -> Optional[str]:
    """Exact ref match, or ref equal to base after optional leading v/v./v."""
    if base in ref_set:
        return base
    base_normalized = _strip_leading_v_prefix(base)
    ver_re = re.compile(
        r'^(?:v\.? ?)?' + re.escape(base_normalized) + r'$', re.IGNORECASE
    )
    candidates = [c for c in ref_set if ver_re.match(c)]
    if candidates:
        return min(candidates, key=lambda x: (len(x), x.lower()))
    return None


def _collect_same_major_minor_refs(
    ref_set: set, base_major: int, base_minor: int
) -> List[Tuple[str, int]]:
    same_maj_min: List[Tuple[str, int]] = []
    for c in ref_set:
        s = c.strip()
        m = _SEMVER_IN_REF.search(s) or _SEMVER_AT_REF_START.match(s)
        if m and int(m.group(1)) == base_major and int(m.group(2)) == base_minor:
            same_maj_min.append((c, int(m.group(3))))
    return same_maj_min


def _try_semver_checkout(base: str, ref_set: set) -> Tuple[bool, str, str]:
    """Return (resolved, ref_or_empty, clarified_version from base semver logic)."""
    _v = _BASE_SEMVER_FOR_CHECKOUT.match(base.strip())
    if not _v:
        return False, "", ""
    base_major, base_minor = int(_v.group(1)), int(_v.group(2))
    base_patch = int(_v.group(3)) if _v.group(3) else 0
    same_maj_min = _collect_same_major_minor_refs(ref_set, base_major, base_minor)
    if same_maj_min:
        exact_patch = [x for x in same_maj_min if x[1] == base_patch]
        if exact_patch:
            ref = min(exact_patch, key=lambda x: (len(x[0]), x[0].lower()))[0]
            clar = (
                f"{base_major}.{base_minor}.{base_patch}"
                if _v.group(3)
                else f"{base_major}.{base_minor}"
            )
            return True, ref, clar
        if _v.group(3):
            return True, "", ""
        ref = max(same_maj_min, key=lambda x: x[1])[0]
        return True, ref, f"{base_major}.{base_minor}"
    if _v.group(3):
        return True, "", ""
    return False, "", ""


def _try_resolve_checkout_base(base: str, ref_set: set) -> Tuple[Optional[str], Optional[str]]:
    """Match one base against ref_set. Returns (ref, clarified); use (None, None) to try next hint."""
    hit = _match_exact_or_v_prefix_ref(base, ref_set)
    if hit is not None:
        return hit, clarified_version_from_oss_version(hit)

    resolved, ref, clar = _try_semver_checkout(base, ref_set)
    if resolved:
        return ref, clar

    # Fallback: find refs that end with the input version (case-insensitive),
    # but only when the match starts at a separator boundary (-, _, /, .)
    # or covers the entire ref. This prevents "2" from matching "3.02".
    # e.g. input "stable202002" matches branch "edk2-stable202002" (boundary: '-')
    _BOUNDARY_CHARS = {'-', '_', '/', '.'}
    base_lower = base.lower()
    containing_refs = []
    for r in ref_set:
        r_lower = r.lower()
        if not r_lower.endswith(base_lower):
            continue
        prefix_len = len(r_lower) - len(base_lower)
        if prefix_len == 0 or r_lower[prefix_len - 1] in _BOUNDARY_CHARS:
            containing_refs.append(r)
    if containing_refs:
        # Prefer the shortest ref (most specific match)
        best = min(containing_refs, key=lambda x: (len(x), x.lower()))
        logger.info(f"Partial match: '{base}' found in ref '{best}'")
        return best, clarified_version_from_oss_version(best)

    return None, None


def decide_checkout(checkout_to="", tag="", branch="", git_url=""):
    ref_dict = get_remote_refs(git_url)
    tag_set = set(ref_dict.get("tags", []))
    branch_set = set(ref_dict.get("branches", []))
    ref_set = tag_set | branch_set
    repo_name = _repo_name_from_git_url(git_url)

    for raw in (tag, branch, checkout_to):
        b = (raw or "").strip()
        if not b:
            continue
        for candidate in _repo_prefixed_version_refs(repo_name, b):
            ref, clar = _try_resolve_checkout_base(candidate, ref_set)
            if ref is not None:
                return ref, clar
        ref, clar = _try_resolve_checkout_base(b, ref_set)
        if ref is not None:
            return ref, clar

    return "", ""


def _git_url_with_http_credentials(git_url, credential_id="", git_token=""):
    """Return git_url with HTTP credentials embedded for ls-remote/clone."""
    if not (credential_id and git_token):
        return git_url
    try:
        parsed = urllib.parse.urlparse(git_url)
        if parsed.username or "@" in (parsed.netloc or ""):
            return git_url
        m = re.match(r"^(ht|f)tp(s?)\:\/\/", git_url)
        if not m:
            return git_url
        protocol = m.group()
        encoded_git_token = urllib.parse.quote(git_token, safe='')
        encoded_credential_id = urllib.parse.quote(credential_id, safe='')
        return git_url.replace(
            protocol, f"{protocol}{encoded_credential_id}:{encoded_git_token}@", 1
        )
    except (ValueError, TypeError, AttributeError) as error:
        logger.info(f"Failed to insert id, token to git url:{error}")
        return git_url


def _resolve_refs_to_checkout(
    checkout_to="",
    tag="",
    branch="",
    git_url="",
    credential_id="",
    git_token="",
):
    auth_url = _git_url_with_http_credentials(git_url, credential_id, git_token)

    # Preserve precedence: tag -> branch -> checkout_to
    resolved, clar = decide_checkout(checkout_to, tag, branch, auth_url)
    if resolved:
        return resolved, clar

    # Fallback when no ref is resolved but checkout_to is provided
    if (checkout_to or "").strip():
        ref = checkout_to.strip()
        return ref, clarified_version_from_oss_version(ref)

    return "", ""


def get_github_ossname(link):
    oss_name = ""
    p = re.compile(r'https?:\/\/github.com\/([^\/]+)\/([^\/\.]+)(\.git)?')
    match = p.match(link)
    if match:
        oss_name = f"{match.group(1)}-{match.group(2)}"
    return oss_name


def get_github_token(git_url):
    github_token = ""
    pattern = r'https://(.*?)@'
    search = re.search(pattern, git_url)
    if search:
        github_token = search.group(1)
    return github_token


def _size_limit_bytes(size_limit_gb: Optional[float]) -> Optional[int]:
    if size_limit_gb is None or size_limit_gb <= 0:
        return None
    return int(float(size_limit_gb) * _BYTES_PER_GB)


def _size_limit_abort_message(
    size_limit_gb: float, when: str, observed_bytes: int = 0
) -> str:
    observed = max(0, int(observed_bytes or 0))
    observed_gb = observed / _BYTES_PER_GB
    return (
        f"Download aborted: temporary directory size exceeded "
        f"limit ({float(size_limit_gb):g} GB) {when} "
        f"(observed {observed_gb:.2f}GB, observed_bytes={observed})."
    )


def _content_length_from_headers(headers) -> int:
    try:
        return int(headers.get("Content-Length") or 0)
    except (TypeError, ValueError):
        return 0


def _raise_if_content_length_over_limit(headers, size_limit_gb: Optional[float], when: str) -> None:
    limit = _size_limit_bytes(size_limit_gb)
    if limit is None:
        return
    content_length = _content_length_from_headers(headers)
    if content_length >= limit:
        raise SizeLimitExceeded(
            _size_limit_abort_message(size_limit_gb, when, content_length)
        )


def _raise_if_bytes_over_limit(num_bytes: int, size_limit_gb: Optional[float], when: str) -> None:
    limit = _size_limit_bytes(size_limit_gb)
    if limit is None:
        return
    if num_bytes >= limit:
        raise SizeLimitExceeded(
            _size_limit_abort_message(size_limit_gb, when, num_bytes)
        )


def _dir_size_bytes(path: str) -> int:
    total = 0
    if not path or not os.path.exists(path):
        return 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            fp = os.path.join(root, name)
            try:
                if os.path.islink(fp):
                    continue
                total += os.path.getsize(fp)
            except OSError:
                continue
    return total


def build_shallow_clone_cmd(git_url: str, target_dir: str, refs_to_checkout: str = "") -> List[str]:
    cmd = [
        "git", "-c", "credential.helper=", "-c", "credential.helper=!",
        "clone", "--depth", "1", "--single-branch",
    ]
    if refs_to_checkout:
        cmd.extend(["--branch", refs_to_checkout])
    cmd.extend([git_url, target_dir])
    return cmd


def _cleanup_target_dir(target_dir: str) -> None:
    try:
        if target_dir and os.path.exists(target_dir):
            shutil.rmtree(target_dir, ignore_errors=True)
    except Exception as e:
        logger.info(f"Failed to remove target dir {target_dir}: {e}")


def run_git_clone_with_size_guard(
    cmd: List[str],
    env: dict,
    target_dir: str,
    size_limit_gb: Optional[float] = None,
    size_check_after_sec: int = SIGNAL_TIMEOUT,
    size_check_interval_sec: int = SIZE_CHECK_INTERVAL_SECONDS,
) -> Tuple[bool, str]:
    """Run git clone via Popen with delayed, periodic, and post-clone size checks.

    After ``size_check_after_sec``, check directory size once while still running.
    If under the limit, re-check every ``size_check_interval_sec``.
    When clone finishes successfully, check the final directory size again.
    Over limit → kill (if needed), cleanup, fail.

    Returns (success, error_message).
    """
    limit = _size_limit_bytes(size_limit_gb)
    try:
        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            stdin=subprocess.DEVNULL,
        )
    except Exception as e:
        return False, str(e)

    def _fail_for_size(elapsed_hint: str, current: int, kill_proc: bool = True) -> Tuple[bool, str]:
        logger.info(
            f"Clone exceeded size limit after {elapsed_hint} "
            f"({current} bytes >= {limit}); aborting."
        )
        if kill_proc:
            try:
                proc.kill()
            except Exception:
                pass
            try:
                proc.communicate(timeout=60)
            except Exception:
                pass
        _cleanup_target_dir(target_dir)
        return False, _size_limit_abort_message(
            size_limit_gb, f"after {elapsed_hint}", current
        )

    stdout = stderr = ""
    try:
        next_timeout = size_check_after_sec
        first_check_done = False
        while True:
            try:
                stdout, stderr = proc.communicate(timeout=next_timeout)
                break
            except subprocess.TimeoutExpired:
                if limit is not None:
                    current = _dir_size_bytes(target_dir)
                    if current >= limit:
                        elapsed = (
                            f"{size_check_after_sec} seconds"
                            if not first_check_done
                            else (
                                f"{size_check_after_sec}s + periodic "
                                f"{size_check_interval_sec}s checks"
                            )
                        )
                        return _fail_for_size(elapsed, current, kill_proc=True)
                first_check_done = True
                # Under limit (or no limit): keep waiting in interval slices
                next_timeout = size_check_interval_sec
    except Exception as e:
        try:
            proc.kill()
        except Exception:
            pass
        return False, str(e)

    if proc.returncode != 0:
        err = (stderr or "").strip() or f"git clone failed (rc={proc.returncode})"
        logger.info(f"Git clone error: {err}")
        return False, err

    if not os.path.isdir(target_dir) or not any(Path(target_dir).iterdir()):
        logger.info(f"No files found in {target_dir} after clone.")
        return False, "No files found after clone."

    # Clone finished within the first wait (or later): still enforce size_limit_gb
    if limit is not None:
        current = _dir_size_bytes(target_dir)
        if current >= limit:
            return _fail_for_size("clone completed", current, kill_proc=False)

    return True, ""


def download_git_repository(
    refs_to_checkout,
    git_url,
    target_dir,
    tag="",
    called_cli=True,
    size_limit_gb: Optional[float] = None,
    credential_id: str = "",
    git_token: str = "",
):
    success = False
    oss_version = ""
    msg = ""

    logger.info(f"Download git url :{git_url}, version:{refs_to_checkout}")

    # Avoid hard process exit from parent SIGALRM while size-guarded clone may run longer
    try:
        if platform.system() != "Windows":
            signal.alarm(0)
    except Exception:
        pass

    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    if platform.system() == "Windows":
        env["GIT_ASKPASS"] = "echo"
    else:
        env["GIT_ASKPASS"] = "/bin/echo"
    env["GIT_CREDENTIAL_HELPER"] = ""
    if "GIT_CONFIG_COUNT" not in env:
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "credential.helper"
        env["GIT_CONFIG_VALUE_0"] = ""
    if "GIT_SSH_COMMAND" not in env:
        env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=no"
    else:
        env["GIT_SSH_COMMAND"] = env["GIT_SSH_COMMAND"] + " -o BatchMode=yes"

    # If target already exists from a failed attempt, empty it before clone
    if os.path.isdir(target_dir) and any(Path(target_dir).iterdir()):
        _cleanup_target_dir(target_dir)
        Path(target_dir).mkdir(parents=True, exist_ok=True)

    cmd = build_shallow_clone_cmd(git_url, target_dir, refs_to_checkout)
    logger.info(f"Shallow clone cmd: {' '.join(cmd)}")
    ok, err = run_git_clone_with_size_guard(
        cmd, env, target_dir, size_limit_gb=size_limit_gb
    )
    if ok:
        success = True
        oss_version = refs_to_checkout or ""
        logger.info(f"Files found in {target_dir} after shallow clone.")
        return success, oss_version, msg

    msg = err
    # If branch/tag clone failed, fall back to default-branch shallow clone
    if refs_to_checkout:
        logger.info(
            f"Shallow clone with ref '{refs_to_checkout}' failed; "
            "retrying default branch shallow clone."
        )
        _cleanup_target_dir(target_dir)
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        fallback_cmd = build_shallow_clone_cmd(git_url, target_dir, "")
        ok2, err2 = run_git_clone_with_size_guard(
            fallback_cmd, env, target_dir, size_limit_gb=size_limit_gb
        )
        if ok2:
            success = True
            oss_version = ""
            msg = ""
            logger.info("Fallback shallow clone succeeded (default branch).")
            return success, oss_version, msg
        msg = err2 or err
    return success, oss_version, msg


def download_git_clone(git_url, target_dir, checkout_to="", tag="", branch="",
                       ssh_key="", id="", git_token="", called_cli=True,
                       size_limit_gb: Optional[float] = None):
    oss_name = get_github_ossname(git_url)
    refs_to_checkout, decided_clarified = _resolve_refs_to_checkout(
        checkout_to, tag, branch, git_url, credential_id=id, git_token=git_token
    )
    msg = ""
    success = True
    oss_version = ""

    try:
        if platform.system() != "Windows":
            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(SIGNAL_TIMEOUT)
        else:
            alarm = Alarm(SIGNAL_TIMEOUT)
            alarm.start()

        Path(target_dir).mkdir(parents=True, exist_ok=True)

        if git_url.startswith("ssh:") and not ssh_key:
            msg = "Private git needs ssh_key"
            success = False
        else:
            if ssh_key:
                logger.info(f"Download git with ssh_key:{git_url}")
                git_ssh_cmd = f'ssh -i {ssh_key}'
                with Git().custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
                    success, oss_version, repo_msg = download_git_repository(
                        refs_to_checkout, git_url, target_dir, tag, called_cli,
                        size_limit_gb=size_limit_gb,
                        credential_id=id, git_token=git_token,
                    )
            else:
                git_url = _git_url_with_http_credentials(git_url, credential_id=id, git_token=git_token)
                success, oss_version, repo_msg = download_git_repository(
                    refs_to_checkout, git_url, target_dir, tag, called_cli,
                    size_limit_gb=size_limit_gb,
                    credential_id=id, git_token=git_token,
                )
            if repo_msg and not success:
                msg = repo_msg

            logger.info(f"git checkout version: {oss_version}")
            refs_to_checkout = oss_version

            if platform.system() != "Windows":
                signal.alarm(0)
            else:
                del alarm
    except Exception as error:
        success = False
        logger.warning(f"git clone - failed: {error}")
        msg = str(error)

    if oss_version:
        clarified_version = decided_clarified or clarified_version_from_oss_version(
            refs_to_checkout
        )
    else:
        clarified_version = ""
    return success, msg, oss_name, refs_to_checkout, clarified_version


def download_wget(link, target_dir, compressed_only, checkout_to, size_limit_gb=None):
    success = False
    msg = ""
    oss_name = ""
    oss_version = ""
    downloaded_file = ""
    resolved_link = ""

    try:
        if platform.system() != "Windows":
            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(SIGNAL_TIMEOUT)
        else:
            alarm = Alarm(SIGNAL_TIMEOUT)
            alarm.start()

        Path(target_dir).mkdir(parents=True, exist_ok=True)

        ret, new_link, oss_name, oss_version, pkg_type = get_downloadable_url(link, checkout_to)
        if ret and new_link:
            link = new_link
        resolved_link = link

        if compressed_only:
            # Check if link ends with known compression extensions
            for ext in compression_extension:
                if link.endswith(ext):
                    success = True
                    break
        else:
            # If get_downloadable_url found a downloadable file, proceed
            if ret:
                success = True
            else:
                # No downloadable file found in package repositories, verify link is downloadable.
                # Some mirrors (e.g. USTC) may 403 or mis-report Content-Type to short probes, while
                # full GET in download_file() succeeds. Skip the probe for obvious direct archive URLs.
                if is_downloadable(link):
                    success = True
                elif _url_looks_like_binary_archive(link):
                    logger.info(
                        "Direct archive URL: probe not OK; will try full download: %s", link
                    )
                    success = True
                else:
                    raise Exception('Not a downloadable link')

        # Fallback: verify link is downloadable for compressed_only case
        if not success:
            if is_downloadable(link) or _url_looks_like_binary_archive(link):
                success = True
            else:
                raise Exception('Not a downloadable link')

        logger.info(f"wget: {link}")
        downloaded_file = download_file(link, target_dir, size_limit_gb=size_limit_gb)
        if platform.system() != "Windows":
            signal.alarm(0)
        else:
            del alarm

        if downloaded_file:
            success = True
            hint = _oss_version_hint_from_wget_link(link, downloaded_file)
            # Keep version resolved by get_downloadable_url() when present.
            # File-name hint is only a fallback when no version was detected.
            if hint and not oss_version:
                oss_version = hint
            logger.debug(f"wget - downloaded: {downloaded_file}")
        else:
            success = False
            msg = f"Download failed: {link}"
            logger.warning("wget - failed: download_file returned no file: %s", link)
    except SizeLimitExceeded as error:
        success = False
        msg = str(error)
        logger.warning(f"wget - size limit: {error}")
        try:
            if platform.system() != "Windows":
                signal.alarm(0)
        except Exception:
            pass
    except Exception as error:
        success = False
        msg = str(error)
        logger.warning(f"wget - failed: {error}")

    return success, downloaded_file, msg, oss_name, oss_version, resolved_link


def _download_file_once(url, target_dir, request_headers=None, size_limit_gb=None):
    """One HTTP download attempt. Raises requests.HTTPError on HTTP failure."""
    final_url = url
    head_headers = {}
    try:
        h = requests.head(
            url, allow_redirects=True, timeout=30, headers=request_headers
        )
        final_url = h.url or url
        head_headers = h.headers
        if h.status_code >= 400:
            final_url = url
            head_headers = {}
        else:
            # Before download: Content-Length size check
            _raise_if_content_length_over_limit(
                head_headers, size_limit_gb, "before download"
            )
    except SizeLimitExceeded:
        raise
    except Exception:
        final_url = url
        head_headers = {}

    local_path = None
    try:
        with requests.get(
            final_url,
            stream=True,
            allow_redirects=True,
            timeout=SIGNAL_TIMEOUT,
            headers=request_headers,
        ) as r:
            r.raise_for_status()
            # GET headers may also expose Content-Length
            _raise_if_content_length_over_limit(
                r.headers, size_limit_gb, "before download"
            )
            content_type = (r.headers.get("content-type") or "").lower()
            if "text/html" in content_type and _url_looks_like_binary_archive(url):
                raise _HtmlWhenBinaryExpected()

            filename = ""
            cd = r.headers.get("Content-Disposition") or head_headers.get(
                "Content-Disposition"
            )
            if cd:
                m_star = re.search(r"filename\*=(?:UTF-8'')?([^;\r\n]+)", cd)
                if m_star:
                    filename = urllib.parse.unquote(m_star.group(1).strip('"\''))
                else:
                    m = re.search(r"filename=([^;\r\n]+)", cd)
                    if m:
                        filename = m.group(1).strip('"\'')
            if not filename:
                final_for_name = r.url or final_url
                filename = os.path.basename(urllib.parse.urlparse(final_for_name).path)
                if not filename:
                    filename = "downloaded_file"
            filename = os.path.basename(filename) or "downloaded_file"

            if os.path.isdir(target_dir):
                local_path = os.path.join(target_dir, filename)
            else:
                local_path = target_dir

            written = 0
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    written += len(chunk)
                    # During download: abort as soon as written bytes exceed limit
                    try:
                        _raise_if_bytes_over_limit(
                            written, size_limit_gb, "during download"
                        )
                    except SizeLimitExceeded:
                        f.close()
                        try:
                            os.remove(local_path)
                        except OSError:
                            pass
                        raise
    except SizeLimitExceeded:
        if local_path:
            try:
                if os.path.exists(local_path):
                    os.remove(local_path)
            except OSError:
                pass
        raise

    # After download: final file size check
    if local_path and os.path.exists(local_path):
        try:
            _raise_if_bytes_over_limit(
                os.path.getsize(local_path), size_limit_gb, "after download"
            )
        except SizeLimitExceeded:
            try:
                os.remove(local_path)
            except OSError:
                pass
            raise
    return local_path


def download_file(url, target_dir, size_limit_gb=None):
    """Download via HTTP(S); retry on 403 or HTML interstitial for archive URLs."""
    attempts = _download_http_header_attempts()
    last_i = len(attempts) - 1
    for i, req_headers in enumerate(attempts):
        try:
            return _download_file_once(
                url, target_dir, req_headers, size_limit_gb=size_limit_gb
            )
        except SizeLimitExceeded:
            raise
        except requests.exceptions.HTTPError as e:
            if (
                e.response is not None
                and e.response.status_code == 403
                and i < last_i
            ):
                logger.info(
                    "download_file: HTTP 403; retrying with alternate User-Agent"
                )
                continue
            logger.warning(f"download_file - failed: {e}")
            return None
        except _HtmlWhenBinaryExpected:
            if i < last_i:
                logger.info(
                    "download_file: archive URL returned HTML; retrying with "
                    "alternate User-Agent"
                )
                continue
            logger.warning(
                "download_file: archive URL still returned HTML after retries"
            )
            return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if i < last_i:
                logger.info(
                    "download_file: connection/timeout %s; retrying with "
                    "alternate User-Agent",
                    e,
                )
                continue
            logger.warning(f"download_file - failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"download_file - failed: {e}")
            return None
    logger.warning("download_file: failed after User-Agent retries")
    return None


def extract_rpm_payload(source_file: str, dest_path: str) -> bool:
    """Unpack RPM/SRPM (cpio payload) into dest_path.

    Tries ``rpm2cpio | cpio -idmv`` (common on Linux), then ``bsdtar``/``tar`` if
    libarchive-backed tar can read the RPM.
    """
    abs_src = os.path.abspath(source_file)
    dest_path = os.path.abspath(dest_path)
    Path(dest_path).mkdir(parents=True, exist_ok=True)

    rpm2cpio = shutil.which("rpm2cpio")
    cpio = shutil.which("cpio")
    if rpm2cpio and cpio:
        p1 = subprocess.Popen(
            [rpm2cpio, abs_src],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=dest_path,
        )
        try:
            try:
                r2 = subprocess.run(
                    [cpio, "-idmv"],
                    stdin=p1.stdout,
                    cwd=dest_path,
                    capture_output=True,
                    text=True,
                    timeout=SIGNAL_TIMEOUT,
                )
            finally:
                if p1.stdout:
                    p1.stdout.close()
            try:
                _, err1 = p1.communicate(timeout=120)
            except subprocess.TimeoutExpired:
                logger.error("rpm2cpio did not finish within timeout")
                return False
        except subprocess.TimeoutExpired:
            logger.error("cpio extraction timed out")
            return False
        finally:
            if p1.poll() is None:
                p1.kill()
            p1.wait()
        if p1.returncode != 0:
            logger.error(
                "rpm2cpio failed (rc=%s): %s",
                p1.returncode,
                (err1 or b"").decode(errors="replace"),
            )
            return False
        if r2.returncode != 0:
            logger.error("cpio failed (rc=%s): %s", r2.returncode, r2.stderr)
            return False
        return True

    for cmd0, args in (
        ("bsdtar", ["bsdtar", "-xf", abs_src, "-C", dest_path]),
        ("tar", ["tar", "-xf", abs_src, "-C", dest_path]),
    ):
        if not shutil.which(cmd0):
            continue
        try:
            r = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=SIGNAL_TIMEOUT,
                check=False,
            )
            if r.returncode == 0:
                return True
            logger.debug("%s extract failed (rc=%s): %s", cmd0, r.returncode, r.stderr)
        except Exception as e:
            logger.debug("%s extract error: %s", cmd0, e)

    logger.error(
        "Cannot extract RPM/SRPM: need rpm2cpio+cpio (e.g. rpm/rpmdevtools) "
        "or bsdtar/tar with RPM support"
    )
    return False


def _fix_extracted_permissions(path: str) -> None:
    try:
        os.chmod(path, os.stat(path).st_mode | 0o755)
    except Exception:
        pass
    for root, dirs, files in os.walk(path, topdown=True):
        dirs[:] = [
            d for d in dirs
            if not os.path.islink(os.path.join(root, d))
        ]
        # Fix dirs before os.walk recurses into them.
        for d in dirs:
            dpath = os.path.join(root, d)
            try:
                os.chmod(dpath, os.stat(dpath).st_mode | 0o755)
            except Exception:
                pass
        for f in files:
            fpath = os.path.join(root, f)
            if os.path.islink(fpath):
                continue
            try:
                os.chmod(fpath, os.stat(fpath).st_mode | 0o644)
            except Exception:
                pass


def _tar_extractall_safe(fname: str, open_mode: str, extract_path: str) -> None:
    try:
        with contextlib.closing(tarfile.open(fname, open_mode)) as tf:
            tf.extractall(path=extract_path)
    except PermissionError as perm_err:
        logger.warning(
            f"Permission error while extracting '{fname}': {perm_err}. "
            f"Fixing permissions and retrying."
        )
        _fix_extracted_permissions(extract_path)
        with contextlib.closing(tarfile.open(fname, open_mode)) as tf:
            members = tf.getmembers()
            for m in members:
                if m.isdir():
                    m.mode = m.mode | 0o755
                elif m.isfile():
                    m.mode = m.mode | 0o644
            tf.extractall(path=extract_path, members=members)
    else:
        # extractall() may restore 0o000/0o666 modes from the archive.
        _fix_extracted_permissions(extract_path)


def _extract_top_level_crates_once(extract_path: str, remove_after_extract: bool) -> bool:
    """After RPM/SRPM unpack: extract each ``*.crate`` in extract_path (non-recursive)."""
    if not extract_path or not os.path.isdir(extract_path):
        return True
    ok = True
    for name in os.listdir(extract_path):
        if not name.lower().endswith(".crate"):
            continue
        cp = os.path.join(extract_path, name)
        if not os.path.isfile(cp):
            continue
        try:
            _tar_extractall_safe(cp, "r:gz", extract_path)
            if remove_after_extract:
                os.remove(cp)
        except Exception as e:
            logger.error(f"Extract crate failed ({cp}): {e}")
            ok = False
    return ok


def extract_compressed_dir(src_dir, target_dir, remove_after_extract=True):
    logger.debug(f"Extract Dir: {src_dir}")
    try:
        files_path = [os.path.join(src_dir, x) for x in os.listdir(src_dir)]
        for fname in files_path:
            extract_compressed_file(fname, target_dir, remove_after_extract, True)
    except Exception as error:
        logger.debug(f"Extract files in dir - failed: {error}")
        return False
    return True


def extract_compressed_file(fname, extract_path, remove_after_extract=True, compressed_only=True):
    success = True
    try:
        is_compressed_file = True
        if os.path.isfile(fname):
            if fname.endswith(".tar.bz2"):
                decompress_bz2(fname, extract_path)
                os.remove(fname)
                fname = os.path.splitext(fname)[0]

            if fname.endswith(".tar.gz") or fname.endswith(".tgz"):
                _tar_extractall_safe(fname, "r:gz", extract_path)
            elif fname.endswith(".tar.xz") or fname.endswith(".tar"):
                _tar_extractall_safe(fname, "r:*", extract_path)
            elif fname.endswith(".zip") or fname.endswith(".jar"):
                unzip(fname, extract_path)
            elif fname.endswith(".bz2"):
                decompress_bz2(fname, extract_path)
            elif fname.endswith(".whl"):
                unzip(fname, extract_path)
            elif fname.endswith(".crate"):
                with contextlib.closing(tarfile.open(fname, "r:gz")) as t:
                    t.extractall(path=extract_path)
            elif fname.lower().endswith(".src.rpm"):
                if not extract_rpm_payload(fname, extract_path):
                    success = False
                    is_compressed_file = False
                elif not _extract_top_level_crates_once(
                    extract_path, remove_after_extract
                ):
                    success = False
            elif fname.lower().endswith(".rpm"):
                if not extract_rpm_payload(fname, extract_path):
                    success = False
                    is_compressed_file = False
                elif not _extract_top_level_crates_once(
                    extract_path, remove_after_extract
                ):
                    success = False
            else:
                try:
                    if zipfile.is_zipfile(fname):
                        unzip(fname, extract_path)
                    elif tarfile.is_tarfile(fname):
                        _tar_extractall_safe(fname, "r:*", extract_path)
                    else:
                        is_compressed_file = False
                        if compressed_only:
                            success = False
                        logger.warning(f"Unsupported file extension: {fname}")
                except Exception as e:
                    success = False
                    is_compressed_file = False
                    logger.debug(f"Magic bytes detection failed: {e}")

            if remove_after_extract and is_compressed_file:
                logger.debug(f"Remove - extracted file: {fname}")
                os.remove(fname)
        else:
            logger.warning(f"Not a file: {fname}")
    except Exception as error:
        logger.error(f"Extract - failed: {error}")
        success = False
    return success


def decompress_bz2(source_file, dest_path):
    try:
        fzip = bz2.BZ2File(source_file)
        data = fzip.read()  # get the decompressed data
        with open(os.path.splitext(source_file)[0], 'wb') as f:
            f.write(data)  # write a uncompressed file

    except Exception as error:
        logger.error(f"Decompress bz2 - failed: {error}")
        return False
    return True


def unzip(source_file, dest_path):
    try:
        fzip = zipfile.ZipFile(source_file, 'r')
        for filename in fzip.namelist():
            fzip.extract(filename, dest_path)
        fzip.close()
    except Exception as error:
        logger.error(f"Unzip - failed: {error}")
        return False
    return True


def get_gem_version(checkout_to, ver_in_url=""):
    gem_ver = ""
    ver_found = False
    if checkout_to:
        ver_found = True
        gem_ver = checkout_to
    elif ver_in_url:
        ver_found = True
        gem_ver = ver_in_url
    return gem_ver, ver_found


def gem_download(link, target_dir, checkout_to):
    ver_in_url = ""
    success = True
    try:
        # EX) https://rubygems.org/gems/json/versions/2.6.2 -> get 'json'
        gem_name = link.split("rubygems.org/gems/")[-1].split('/')[0]
        # Ex) if version info. is included in url, json/versions/2.6.2 -> get '2.6.2'
        if 'versions/' in link:
            ver_in_url = link.split('versions/')[-1]
        gem_ver, ver_found = get_gem_version(checkout_to, ver_in_url)

        # gem fetch
        if ver_found:
            fetch_cmd = ['gem', 'fetch', gem_name, '-v', gem_ver]
        else:
            fetch_cmd = ['gem', 'fetch', gem_name]
        fetch_result = subprocess.check_output(fetch_cmd, universal_newlines=True)
        fetch_result = fetch_result.replace('\n', '').split(' ')[-1]
        downloaded_gem = f"{fetch_result}.gem"
        if not os.path.isfile(downloaded_gem):
            success = False
        else:
            # gem unpack
            subprocess.check_output(['gem', 'unpack', downloaded_gem], universal_newlines=True)
            # move unpacked file to target directory
            shutil.move(fetch_result, target_dir)
    except Exception as error:
        success = False
        logger.warning(f"gem download - failed: {error}")
    return success


def main():
    parser = argparse.ArgumentParser(description='FOSSLight Downloader', prog='fosslight_download', add_help=False)
    parser.add_argument('-h', '--help', help='Print help message', action='store_true', dest='help')
    parser.add_argument('-s', '--source', help='Source link to download', type=str, dest='source')
    parser.add_argument('-t', '--target_dir', help='Target directory', type=str, dest='target_dir', default="")
    parser.add_argument('-d', '--log_dir', help='Directory to save log file', type=str, dest='log_dir', default="")
    parser.add_argument('-c', '--checkout_to', help='Checkout to  branch or tag', type=str, dest='checkout_to', default="")
    parser.add_argument('-z', '--compressed_only', help='Unzip only compressed file',
                        action='store_true', dest='compressed_only', default=False)
    parser.add_argument('-o', '--output', help='Generate output file', action='store_true', dest='output', default=False)
    parser.add_argument('-l', '--size-limit', help='Max download size in GB (omit for unlimited)',
                        type=float, dest='size_limit', default=None)

    src_link = ""
    target_dir = os.getcwd()
    log_dir = os.getcwd()
    checkout_to = ""
    compressed_only = False
    output = False
    size_limit_gb = None

    try:
        args = parser.parse_args()
    except SystemExit:
        sys.exit(0)

    if args.help:
        print_help_msg_download()
    if args.source:
        src_link = args.source
    if args.target_dir:
        target_dir = args.target_dir
    if args.log_dir:
        log_dir = args.log_dir
    if args.checkout_to:
        checkout_to = args.checkout_to
    if args.compressed_only:
        compressed_only = args.compressed_only
    if args.output:
        output = args.output
    if args.size_limit is not None:
        size_limit_gb = args.size_limit

    if not src_link:
        print_help_msg_download()
    else:
        cli_download_and_extract(src_link, target_dir, log_dir, checkout_to,
                                 compressed_only, "", "", "", False,
                                 output, size_limit_gb=size_limit_gb)


if __name__ == '__main__':
    main()
