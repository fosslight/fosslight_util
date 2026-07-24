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

# Some mirrors (e.g. mirrors.ustc.edu.cn) return 403 for python-requests' default
# User-Agent, or 200 with a small text/html interstitial. Start with a curl-style UA
# (widely accepted for file downloads), then browser, then default requests as fallback.
_HTTP_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_HTTP_CURL_LIKE_USER_AGENT = "curl/8.7.1"


class _HtmlWhenBinaryExpected(Exception):
    """Server returned HTML for a URL that should be a binary archive; try another client."""


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


def _setup_download_alarm(timeout=SIGNAL_TIMEOUT):
    if platform.system() == "Windows":
        alarm = Alarm(timeout)
        alarm.start()
        return alarm
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout)
    return None


def _clear_download_alarm(alarm=None):
    if platform.system() != "Windows":
        signal.alarm(0)
    else:
        del alarm


class DownloadFailure(Exception):
    def __init__(self, message, status_code=None, reason=None):
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason or "download_failed"


def _classify_download_failure(status_code=None, error=None):
    if status_code == 404:
        return "not_found"
    if status_code is not None and status_code >= 400:
        return "http_error"
    if isinstance(error, _HtmlWhenBinaryExpected):
        return "html_interstitial"
    if isinstance(error, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return "network_error"
    return "download_failed"


def _build_download_failure_message(failure_reason, link):
    messages = {
        "not_found": f"404 Not Found: {link}",
        "http_error": f"HTTP error while downloading: {link}",
        "html_interstitial": f"HTML interstitial while downloading: {link}",
        "network_error": f"Network error while downloading: {link}",
    }
    return messages.get(failure_reason, f"Download failed: {link}")


def alarm_handler(signum, frame):
    logger.warning("download timeout! (%d sec)", SIGNAL_TIMEOUT)
    raise TimeOutException(f'Timeout ({SIGNAL_TIMEOUT} sec)', 1)


def _build_git_environment() -> dict:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "echo" if platform.system() == "Windows" else "/bin/echo"
    env["GIT_CREDENTIAL_HELPER"] = ""
    if "GIT_CONFIG_COUNT" not in env:
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "credential.helper"
        env["GIT_CONFIG_VALUE_0"] = ""
    if "GIT_SSH_COMMAND" not in env:
        env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=no"
    else:
        env["GIT_SSH_COMMAND"] = env["GIT_SSH_COMMAND"] + " -o BatchMode=yes"
    return env


def _compose_download_result_message(git_message: str, wget_message: str, is_rubygems: bool, success: bool) -> str:
    if is_rubygems:
        return f"gem download: {success}"
    if git_message:
        if wget_message:
            return f"git fail: {git_message}"
        return f"git fail: {git_message}, wget success"
    if wget_message:
        return f"wget fail: {wget_message}"
    return ""


def is_downloadable(url):
    """Probe URL; retry with alternate User-Agents on 403 or HTML body for archive URLs.

    Repository URLs and HTML pages may legitimately return text/html during a lightweight
    probe even though a real download attempt could still succeed. Keep the probe quiet in
    those cases so later download failures report the real reason instead of an overly
    misleading preflight warning.
    """
    attempts = _download_http_header_attempts()
    last_i = len(attempts) - 1
    for i, headers in enumerate(attempts):
        try:
            with requests.get(
                url, stream=True, allow_redirects=True, timeout=10, headers=headers
            ) as r:
                if r.status_code == 403 and i < last_i:
                    continue
                if r.status_code == 404:
                    logger.warning("is_downloadable - 404 Not Found: %s", url)
                    return False
                if r.status_code >= 400:
                    logger.warning("is_downloadable - HTTP %s: %s", r.status_code, url)
                    return False
                content_type = r.headers.get('content-type', '').lower()
                if 'text/html' in content_type:
                    if _url_looks_like_binary_archive(url) and i < last_i:
                        continue
                    if _url_looks_like_binary_archive(url):
                        logger.info(
                            "is_downloadable: archive URL returned HTML; will rely on full download attempt"
                        )
                    else:
                        logger.debug(
                            "is_downloadable: HTML response for non-archive URL; will rely on full download attempt: %s",
                            url,
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
                             output: bool = False) -> Tuple[bool, str, str, str, str]:
    global logger

    success = True
    msg = ""
    msg_wget = ""
    oss_name = ""
    oss_version = ""
    downloaded_link = ""
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
                ssh_key, id, git_token, called_cli)
            link = change_ssh_link_to_https(link)
            if success_git:
                downloaded_link = link
            if (not is_rubygems) and (not success_git):
                if os.path.isfile(target_dir):
                    shutil.rmtree(target_dir)

                success, downloaded_file, msg_wget, oss_name, oss_version, resolved_link = download_wget(
                    link, target_dir, compressed_only, checkout_to
                )
                if success and downloaded_file:
                    extraction_ok = extract_compressed_file(
                        downloaded_file, target_dir, True, compressed_only
                    )
                    if extraction_ok:
                        downloaded_link = resolved_link
                    else:
                        success = False
                        if not msg_wget:
                            msg_wget = "extraction failed"
            # Download from rubygems.org
            elif is_rubygems and shutil.which("gem"):
                success = gem_download(link, target_dir, checkout_to)
                if success:
                    downloaded_link = link
        msg = _compose_download_result_message(msg, msg_wget, is_rubygems, success)

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
        env = _build_git_environment()
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


def _run_git_command(command, env, timeout):
    return subprocess.run(
        command,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
    )


def _format_git_error_message(error_message: str) -> str:
    if not error_message:
        return "Git clone failed"

    cleaned = error_message.strip().replace("\r", "").replace("\n", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if cleaned.startswith("fatal:"):
        cleaned = cleaned[len("fatal:"):].strip()

    if cleaned.startswith("GitError:"):
        cleaned = cleaned[len("GitError:"):].strip()

    if cleaned.startswith("Cmd('git"):
        cleaned = cleaned.split("Cmd('git", 1)[0].strip()

    if cleaned.startswith("Command ") and " returned non-zero exit status" in cleaned:
        cleaned = cleaned.split(" returned non-zero exit status", 1)[0].strip()

    if cleaned.startswith("command not found"):
        return "Git command not found"

    if "already exists and is not an empty directory" in cleaned:
        return "destination path already exists and is not an empty directory"

    if "not a git repository" in cleaned.lower():
        return "repository is not a valid Git repository"

    if "could not read from remote repository" in cleaned.lower():
        return "could not read from remote repository"

    if "authentication failed" in cleaned.lower():
        return "authentication failed"

    if "connection timed out" in cleaned.lower():
        return "connection timed out"

    if "timed out" in cleaned.lower():
        return "operation timed out"

    if cleaned.startswith("error:"):
        cleaned = cleaned[len("error:"):].strip()

    return cleaned


def download_git_repository(refs_to_checkout, git_url, target_dir, tag, called_cli=True):
    success = False
    oss_version = ""
    error_message = ""

    logger.info(f"Download git url :{git_url}, version:{refs_to_checkout}")
    env = _build_git_environment()

    if refs_to_checkout:
        try:
            # For tags, we need full history. For branches, shallow clone is possible but
            # we use full clone to ensure compatibility with all cases
            # Use subprocess to ensure environment variables are properly passed
            cmd = ["git", "-c", "credential.helper=", "-c", "credential.helper=!", "clone", git_url, target_dir]
            result = _run_git_command(cmd, env, 600)
            if result.returncode == 0:
                # Checkout the specific branch or tag
                checkout_cmd = ["git", "-C", target_dir, "checkout", refs_to_checkout]
                checkout_result = _run_git_command(checkout_cmd, env, 60)
                if checkout_result.returncode == 0:
                    if any(Path(target_dir).iterdir()):
                        success = True
                        oss_version = refs_to_checkout
                        logger.info(f"Files found in {target_dir} after clone and checkout.")
                    else:
                        logger.info(f"No files found in {target_dir} after clone.")
                        success = False
                else:
                    logger.info(f"Git checkout error: {checkout_result.stderr}")
                    error_message = checkout_result.stderr.strip() or "Git checkout failed"
                    # Clone succeeded but checkout failed (e.g. non-existent ref):
                    # repo has default branch; treat as success with empty version
                    if any(Path(target_dir).iterdir()):
                        success = True
                        oss_version = ""
                        logger.info("Checkout failed; keeping default branch.")
            else:
                error_message = result.stderr.strip() or "Git clone failed"
                logger.info(f"Git clone error: {error_message}")
                success = False
        except subprocess.TimeoutExpired:
            error_message = "Git clone timeout"
            logger.info(error_message)
            success = False
        except Exception as e:
            error_message = str(e)
            logger.info(f"Git clone error:{e}")
            success = False

    if not success:
        try:
            # Use subprocess to ensure environment variables are properly passed
            # No checkout needed, so shallow clone is sufficient
            cmd = [
                "git", "-c", "credential.helper=", "-c", "credential.helper=!",
                "clone", "--depth", "1", git_url, target_dir
            ]
            result = _run_git_command(cmd, env, 600)
            if result.returncode == 0:
                if any(Path(target_dir).iterdir()):
                    success = True
                else:
                    logger.info(f"No files found in {target_dir} after clone.")
                    success = False
            else:
                error_message = result.stderr.strip() or "Git clone failed"
                logger.info(f"Git clone error: {error_message}")
                success = False
        except subprocess.TimeoutExpired:
            error_message = "Git clone timeout"
            logger.info(error_message)
            success = False
        except Exception as e:
            error_message = str(e)
            logger.info(f"Git clone error:{e}")
            success = False
    return success, oss_version, error_message


def download_git_clone(git_url, target_dir, checkout_to="", tag="", branch="",
                       ssh_key="", id="", git_token="", called_cli=True):
    oss_name = get_github_ossname(git_url)
    refs_to_checkout, decided_clarified = _resolve_refs_to_checkout(
        checkout_to, tag, branch, git_url, credential_id=id, git_token=git_token
    )
    msg = ""
    success = True
    oss_version = ""

    try:
        alarm = _setup_download_alarm(SIGNAL_TIMEOUT)

        Path(target_dir).mkdir(parents=True, exist_ok=True)

        if git_url.startswith("ssh:") and not ssh_key:
            msg = "Private git needs ssh_key"
            success = False
        else:
            if ssh_key:
                logger.info(f"Download git with ssh_key:{git_url}")
                git_ssh_cmd = f'ssh -i {ssh_key}'
                with Git().custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
                    success, oss_version, git_error = download_git_repository(
                        refs_to_checkout,
                        git_url,
                        target_dir,
                        tag,
                        called_cli
                    )
            else:
                git_url = _git_url_with_http_credentials(git_url, credential_id=id, git_token=git_token)
                success, oss_version, git_error = download_git_repository(
                    refs_to_checkout,
                    git_url,
                    target_dir,
                    tag,
                    called_cli
                )

            if not success and not msg and git_error:
                msg = _format_git_error_message(git_error)

            logger.info(f"git checkout version: {oss_version}")
            refs_to_checkout = oss_version

            _clear_download_alarm(alarm)
    except Exception as error:
        success = False
        logger.warning(f"git clone - failed: {error}")
        msg = str(error)

    if not msg and not success and not oss_version:
        msg = "Git clone failed"

    if oss_version:
        clarified_version = decided_clarified or clarified_version_from_oss_version(
            refs_to_checkout
        )
    else:
        clarified_version = ""
    return success, msg, oss_name, refs_to_checkout, clarified_version


def download_wget(link, target_dir, compressed_only, checkout_to):
    success = False
    msg = ""
    oss_name = ""
    oss_version = ""
    downloaded_file = ""
    resolved_link = ""

    try:
        alarm = _setup_download_alarm(SIGNAL_TIMEOUT)

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
            # If get_downloadable_url found a downloadable file, proceed.
            # Otherwise, rely on the full download attempt to decide whether the URL is usable.
            # A lightweight probe can return HTML for repository pages and still allow a real
            # download attempt to succeed or fail with the correct reason.
            if ret:
                success = True
            else:
                probe_ok = is_downloadable(link)
                if probe_ok:
                    success = True
                else:
                    logger.info(
                        "Link probe not conclusive; will try full download: %s", link
                    )
                    success = True

        # Fallback: verify link is downloadable for compressed_only case
        if not success:
            if is_downloadable(link) or _url_looks_like_binary_archive(link):
                success = True
            else:
                raise Exception('Not a downloadable link')

        logger.info(f"wget: {link}")
        downloaded_file, failure_reason = download_file(link, target_dir)
        _clear_download_alarm(alarm)

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
            msg = _build_download_failure_message(failure_reason, link)
            logger.warning("wget - failed: %s", msg)
    except Exception as error:
        success = False
        msg = str(error)
        logger.warning(f"wget - failed: {error}")

    return success, downloaded_file, msg, oss_name, oss_version, resolved_link


def _download_file_once(url, target_dir, request_headers=None):
    """One HTTP download attempt. Raises DownloadFailure on HTTP failure."""
    final_url = url
    head_headers = {}
    try:
        h = requests.head(
            url, allow_redirects=True, timeout=30, headers=request_headers
        )
        final_url = h.url or url
        head_headers = h.headers
        if h.status_code >= 400:
            raise DownloadFailure(
                f"HTTP {h.status_code}",
                status_code=h.status_code,
                reason=_classify_download_failure(status_code=h.status_code),
            )
    except DownloadFailure:
        raise
    except Exception:
        final_url = url
        head_headers = {}

    with requests.get(
        final_url,
        stream=True,
        allow_redirects=True,
        timeout=SIGNAL_TIMEOUT,
        headers=request_headers,
    ) as r:
        if r.status_code >= 400:
            raise DownloadFailure(
                f"HTTP {r.status_code}",
                status_code=r.status_code,
                reason=_classify_download_failure(status_code=r.status_code),
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
        if os.path.isdir(target_dir):
            local_path = os.path.join(target_dir, filename)
        else:
            local_path = target_dir

        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_path


def download_file(url, target_dir):
    """Download via HTTP(S); retry on 403 or HTML interstitial for archive URLs."""
    attempts = _download_http_header_attempts()
    last_i = len(attempts) - 1
    for i, req_headers in enumerate(attempts):
        try:
            return _download_file_once(url, target_dir, req_headers), None
        except DownloadFailure as e:
            if e.status_code == 403 and i < last_i:
                logger.info(
                    "download_file: HTTP 403; retrying with alternate User-Agent"
                )
                continue
            logger.warning("download_file - failed: %s", e)
            return None, _classify_download_failure(status_code=e.status_code, error=e)
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
            return None, "html_interstitial"
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if i < last_i:
                logger.info(
                    "download_file: connection/timeout %s; retrying with "
                    "alternate User-Agent",
                    e,
                )
                continue
            logger.warning(f"download_file - failed: {e}")
            return None, "network_error"
        except Exception as e:
            logger.warning(f"download_file - failed: {e}")
            return None, "download_failed"
    logger.warning("download_file: failed after User-Agent retries")
    return None, "download_failed"


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
        if not os.path.exists(fname):
            logger.warning(f"Not a file: {fname}")
            return False
        if os.path.isdir(fname):
            logger.warning(f"Path is a directory, not an archive: {fname}")
            return False
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

    src_link = ""
    target_dir = os.getcwd()
    log_dir = os.getcwd()
    checkout_to = ""
    compressed_only = False
    output = False

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

    if not src_link:
        print_help_msg_download()
    else:
        cli_download_and_extract(src_link, target_dir, log_dir, checkout_to,
                                 compressed_only, "", "", "", False,
                                 output)


if __name__ == '__main__':
    main()
