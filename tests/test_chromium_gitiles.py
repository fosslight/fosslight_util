# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os

from fosslight_util.download import (
    cli_download_and_extract,
    download_wget,
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
    monkeypatch.setattr(download_module, "extract_compressed_file", lambda *_args, **_kwargs: True)

    log_dir = tmp_path / "log"
    log_dir.mkdir()
    success, msg, _, oss_version, clarified_version = cli_download_and_extract(
        _BORINGSSL, str(tmp_path / "out"), str(log_dir), output=True,
    )

    assert success is True, msg
    assert cloned == []
    assert oss_version == "114.0.5735.358"
    assert clarified_version == "114.0.5735.358"
    with open(log_dir / "fosslight_download_output.json", encoding="utf-8") as output_file:
        result = json.load(output_file)
    assert result["link"] == "https://cdn.example/boringssl.tar.gz"
    assert result["oss_version"] == "114.0.5735.358"
    assert result["clarified_version"] == "114.0.5735.358"


def test_archive_failure_clones_repository(tmp_path, monkeypatch):
    from fosslight_util import download as download_module

    _silence_log(monkeypatch, download_module)
    cloned = {}

    monkeypatch.setattr(
        download_module,
        "download_wget",
        lambda *_args, **_kwargs: (False, "", "archive failed", "", "", ""),
    )

    def fake_clone(git_url, _target_dir, checkout_to, *_args, **_kwargs):
        cloned["url"] = git_url
        cloned["ref"] = checkout_to
        return True, "", "src", "resolved-by-git", "resolved-by-git"

    monkeypatch.setattr(download_module, "download_git_clone", fake_clone)

    log_dir = tmp_path / "log"
    log_dir.mkdir()
    success, msg, _, oss_version, clarified_version = cli_download_and_extract(
        _BORINGSSL, str(tmp_path / "out"), str(log_dir), output=True,
    )

    assert success is True, msg
    assert cloned == {"url": _REPO, "ref": "114.0.5735.358"}
    assert oss_version == "114.0.5735.358"
    assert clarified_version == "114.0.5735.358"
    with open(log_dir / "fosslight_download_output.json", encoding="utf-8") as output_file:
        result = json.load(output_file)
    assert result["link"] == _REPO
    assert result["oss_version"] == "114.0.5735.358"
    assert result["clarified_version"] == "114.0.5735.358"


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
