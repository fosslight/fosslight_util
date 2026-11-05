# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os

from fosslight_util.download import (
    _gitiles_clone_attempts,
    cli_download_and_extract,
    download_wget,
    gitiles_link_version,
    parse_chromium_gitiles_path,
)

_BORINGSSL = (
    "https://chromium.googlesource.com/chromium/src/"
    "+/refs/tags/114.0.5735.358/third_party/boringssl/"
)
_BORINGSSL_ARCHIVE = (
    "https://chromium.googlesource.com/chromium/src/+archive/"
    "refs/tags/114.0.5735.358/third_party/boringssl.tar.gz"
)
_REPO = "https://chromium.googlesource.com/chromium/src"


def test_parses_refs_tags_subdirectory():
    assert parse_chromium_gitiles_path(_BORINGSSL) == (
        _REPO,
        _BORINGSSL_ARCHIVE,
        "114.0.5735.358",
        "tag",
    )


def test_parses_bare_revision_and_encoded_plus():
    encoded = (
        "https://chromium.googlesource.com/chromium/src/"
        "%2B/84.0.4147.135/third_party/crashpad/"
    )
    assert parse_chromium_gitiles_path(encoded) == (
        _REPO,
        "https://chromium.googlesource.com/chromium/src/+archive/"
        "84.0.4147.135/third_party/crashpad.tar.gz",
        "84.0.4147.135",
        "name",
    )


def test_ignores_other_hosts_and_revision_without_subdirectory():
    android = (
        "https://android.googlesource.com/platform/bionic/"
        "+/refs/tags/android-14.0.0_r1/libc/"
    )
    revision_only = (
        "https://chromium.googlesource.com/chromium/src/"
        "+/refs/tags/114.0.5735.358"
    )
    assert parse_chromium_gitiles_path(android) is None
    assert parse_chromium_gitiles_path(revision_only) is None
    assert parse_chromium_gitiles_path(_REPO) is None
    assert parse_chromium_gitiles_path(_BORINGSSL_ARCHIVE) is None


def _silence_log(monkeypatch, module):
    monkeypatch.setattr(
        module,
        "init_log",
        lambda *_args, **_kwargs: (logging.getLogger("test-gitiles"), {}),
    )


def test_archive_success_does_not_clone(tmp_path, monkeypatch):
    from fosslight_util import download as download_module

    _silence_log(monkeypatch, download_module)
    cloned = []

    def fake_wget(link, target_dir, *_args, **_kwargs):
        archive = os.path.join(target_dir, "boringssl.tar.gz")
        os.makedirs(target_dir, exist_ok=True)
        with open(archive, "wb") as output:
            output.write(b"archive")
        return True, archive, "", "", "114.0.5735.358", (
            "https://cdn.example/boringssl.tar.gz"
        )

    monkeypatch.setattr(download_module, "download_wget", fake_wget)
    monkeypatch.setattr(
        download_module,
        "download_git_clone",
        lambda *_args, **_kwargs: cloned.append(_args) or (False, "cloned", "", "", ""),
    )
    extracted = {}

    def fake_extract(*args, **_kwargs):
        extracted["args"] = args
        return True

    monkeypatch.setattr(download_module, "extract_compressed_file", fake_extract)

    log_dir = tmp_path / "log"
    log_dir.mkdir()
    success, msg, _, oss_version, clarified_version = cli_download_and_extract(
        _BORINGSSL, str(tmp_path / "out"), str(log_dir), output=True,
    )

    assert success is True, msg
    assert cloned == []
    assert extracted["args"][3] is True
    assert oss_version == "114.0.5735.358"
    assert clarified_version == "114.0.5735.358"
    with open(log_dir / "fosslight_download_output.json", encoding="utf-8") as output_file:
        result = json.load(output_file)
    assert result["link"] == "https://cdn.example/boringssl.tar.gz"
    assert result["oss_version"] == "114.0.5735.358"
    assert result["clarified_version"] == "114.0.5735.358"


def test_link_version_is_the_numeric_segment():
    releases = (
        "https://chromium.googlesource.com/chromium/src/"
        "+/refs/heads/releases/114/third_party/boringssl/"
    )
    assert gitiles_link_version(releases) == "114"
    assert gitiles_link_version(_BORINGSSL) == "114.0.5735.358"
    assert gitiles_link_version(
        "https://chromium.googlesource.com/chromium/src/"
        "+/refs/heads/main/third_party/boringssl/"
    ) == ""
    assert _gitiles_clone_attempts("114", "9.9") == [
        ("114", False),
        ("9.9", False),
        ("", True),
    ]
    assert _gitiles_clone_attempts("", "") == [("", True)]


def test_archive_failure_checks_out_link_version(tmp_path, monkeypatch):
    from fosslight_util import download as download_module

    _silence_log(monkeypatch, download_module)
    cloned = []

    monkeypatch.setattr(
        download_module,
        "download_wget",
        lambda *_args, **_kwargs: (False, "", "archive failed", "", "", ""),
    )

    def fake_clone(git_url, _target_dir, checkout_to, tag, branch, *_args, **kwargs):
        cloned.append({
            "url": git_url,
            "ref": checkout_to,
            "tag": tag,
            "branch": branch,
            "fallback": kwargs.get("allow_default_branch_fallback"),
        })
        return True, "", "src", "114.0.5735.358", "114.0.5735.358"

    monkeypatch.setattr(download_module, "download_git_clone", fake_clone)

    log_dir = tmp_path / "log"
    log_dir.mkdir()
    success, msg, _, oss_version, clarified_version = cli_download_and_extract(
        _BORINGSSL, str(tmp_path / "out"), str(log_dir), output=True,
    )

    assert success is True, msg
    assert cloned == [{
        "url": _REPO,
        "ref": "114.0.5735.358",
        "tag": "",
        "branch": "",
        "fallback": False,
    }]
    assert oss_version == "114.0.5735.358"
    assert clarified_version == "114.0.5735.358"
    with open(log_dir / "fosslight_download_output.json", encoding="utf-8") as output_file:
        result = json.load(output_file)
    assert result["link"] == _REPO
    assert result["oss_version"] == "114.0.5735.358"
    assert result["clarified_version"] == "114.0.5735.358"


def test_parses_commit_and_branch_kinds():
    commit_url = (
        "https://chromium.googlesource.com/chromium/src/"
        "+/abcdef0123456789/third_party/boringssl/"
    )
    branch_url = (
        "https://chromium.googlesource.com/chromium/src/"
        "+/refs/heads/main/third_party/boringssl/"
    )
    assert parse_chromium_gitiles_path(commit_url)[2:] == ("abcdef0123456789", "commit")
    assert parse_chromium_gitiles_path(branch_url)[2:] == ("main", "branch")


def test_releases_path_checks_out_114_then_checkout_then_default(tmp_path, monkeypatch):
    from fosslight_util import download as download_module

    _silence_log(monkeypatch, download_module)
    calls = []
    releases = (
        "https://chromium.googlesource.com/chromium/src/"
        "+/refs/heads/releases/114/third_party/boringssl/;tag=other"
    )
    monkeypatch.setattr(
        download_module,
        "download_wget",
        lambda *_args, **_kwargs: (False, "", "archive failed", "", "", ""),
    )

    def fake_clone(_git_url, _target_dir, checkout_to, tag, branch, *_args, **kwargs):
        calls.append((checkout_to, tag, branch, kwargs.get("allow_default_branch_fallback")))
        if checkout_to == "9.9":
            return True, "", "src", "9.9", "9.9"
        return False, f"miss {checkout_to}", "", "", ""

    monkeypatch.setattr(download_module, "download_git_clone", fake_clone)
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    success, msg, _, oss_version, clarified = cli_download_and_extract(
        releases, str(tmp_path / "out"), str(log_dir), checkout_to="9.9", output=True,
    )

    assert success is True, msg
    assert calls == [
        ("114", "", "", False),
        ("9.9", "", "", False),
    ]
    assert oss_version == "9.9"
    assert clarified == "9.9"


def test_default_branch_leaves_version_blank(tmp_path, monkeypatch):
    from fosslight_util import download as download_module

    _silence_log(monkeypatch, download_module)
    calls = []
    releases = (
        "https://chromium.googlesource.com/chromium/src/"
        "+/refs/heads/releases/114/third_party/boringssl/"
    )
    monkeypatch.setattr(
        download_module,
        "download_wget",
        lambda *_args, **_kwargs: (False, "", "archive failed", "", "", ""),
    )

    def fake_clone(_git_url, _target_dir, checkout_to, *_args, **kwargs):
        calls.append((checkout_to, kwargs.get("allow_default_branch_fallback")))
        if checkout_to == "":
            return True, "", "src", "", ""
        return False, "miss", "", "", ""

    monkeypatch.setattr(download_module, "download_git_clone", fake_clone)
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    success, msg, _, oss_version, clarified = cli_download_and_extract(
        releases, str(tmp_path / "out"), str(log_dir), output=True,
    )

    assert success is True, msg
    assert calls == [("114", False), ("", True)]
    assert oss_version == ""
    assert clarified == ""
    with open(log_dir / "fosslight_download_output.json", encoding="utf-8") as output_file:
        result = json.load(output_file)
    assert result["link"] == _REPO
    assert result["oss_version"] == ""
    assert result["clarified_version"] == ""


def test_fallback_keeps_preexisting_files(tmp_path, monkeypatch):
    from fosslight_util import download as download_module

    _silence_log(monkeypatch, download_module)
    called = []
    monkeypatch.setattr(
        download_module,
        "download_wget",
        lambda *_args, **_kwargs: (False, "", "archive failed", "", "", ""),
    )
    monkeypatch.setattr(
        download_module,
        "download_git_clone",
        lambda *_args, **_kwargs: called.append("clone") or (True, "", "", "", ""),
    )
    out = tmp_path / "out"
    out.mkdir()
    kept = out / "keep.txt"
    kept.write_text("mine")
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    success, msg, _, _, _ = cli_download_and_extract(
        _BORINGSSL, str(out), str(log_dir), output=True,
    )

    assert success is False
    assert "not empty" in msg
    assert kept.read_text() == "mine"
    assert called == []


def test_download_wget_keeps_redirected_url(tmp_path, monkeypatch):
    from fosslight_util import download as download_module

    monkeypatch.setattr(
        download_module,
        "get_downloadable_url",
        lambda *_args, **_kwargs: (True, "https://example.com/pkg.tar.gz", "pkg", "1.0", ""),
    )

    def fake_download_file(_url, target_dir, size_limit_gb=None):
        path = os.path.join(target_dir, "pkg.tar.gz")
        with open(path, "wb") as output:
            output.write(b"not-html")
        return path, "https://cdn.example/pkg-1.0.tar.gz"

    monkeypatch.setattr(download_module, "download_file", fake_download_file)

    success, _path, msg, _name, _version, resolved = download_wget(
        "https://example.com/pkg.tar.gz", str(tmp_path), False, "",
    )

    assert success is True, msg
    assert resolved == "https://cdn.example/pkg-1.0.tar.gz"
