# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for wget-path oss_version / clarified_version hints from URL and filename."""

import json
import logging

import pytest

from fosslight_util import download as download_module
from fosslight_util.download import (
    cli_download_and_extract,
    clarified_version_from_oss_version,
    _oss_version_hint_from_wget_link,
)
from fosslight_util import _get_downloadable_url as downloadable_url


@pytest.mark.parametrize(
    "link,downloaded_file,expected_hint",
    [
        # crates.io (API URL must not use path segment "download" as version)
        (
            "https://crates.io/api/v1/crates/transpose/0.2.3/download",
            "/tmp/transpose-0.2.3.crate",
            "0.2.3",
        ),
        (
            "https://crates.io/crates/transpose/0.2.3",
            "",
            "0.2.3",
        ),
        # GNU mirror–style tarball URL
        (
            "https://mirrors.ustc.edu.cn/gnu/bison/bison-3.8.2.tar.xz",
            "/dl/bison-3.8.2.tar.xz",
            "3.8.2",
        ),
        # GitHub release archive (basename is vX.Y.Z.tar.gz; hint keeps leading v)
        (
            "https://github.com/Kitware/CMake/archive/refs/tags/v3.28.3.tar.gz",
            "/t/v3.28.3.tar.gz",
            "v3.28.3",
        ),
        # PyPI file URL (basename package-version.tar.gz)
        (
            "https://files.pythonhosted.org/packages/source/r/requests/requests-2.31.0.tar.gz",
            "/t/requests-2.31.0.tar.gz",
            "2.31.0",
        ),
        # X.Org individual lib
        (
            "https://www.x.org/releases/individual/lib/libXdmcp-1.1.4.tar.xz",
            "/t/libXdmcp-1.1.4.tar.xz",
            "1.1.4",
        ),
        # npm registry tarball (often ends with package-version.tgz)
        (
            "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz",
            "/t/lodash-4.17.21.tgz",
            "4.17.21",
        ),
        # mvnrepository.com page URL (version is last path segment; four-part Maven version)
        (
            "https://mvnrepository.com/artifact/org.xerial.snappy/snappy-java/1.1.7.7",
            "",
            "1.1.7.7",
        ),
        # Generic: path ends with /download but real version only in filename
        (
            "https://example.com/releases/download",
            "/build/myproject-2.0.0.tar.xz",
            "2.0.0",
        ),
        # crates.io API takes precedence over misleading local path
        (
            "https://crates.io/api/v1/crates/serde/1.0.190/download",
            "/wrong/path.txt",
            "1.0.190",
        ),
    ],
)
def test_oss_version_hint_from_wget_link(link, downloaded_file, expected_hint):
    got = _oss_version_hint_from_wget_link(link, downloaded_file)
    assert got == expected_hint, f"hint got {got!r} expected {expected_hint!r}"


@pytest.mark.parametrize(
    "hint,expected_clarified",
    [
        ("0.2.3", "0.2.3"),
        ("3.8.2", "3.8.2"),
        ("2.31.0", "2.31.0"),
        ("4.17.21", "4.17.21"),
        ("1.1.4", "1.1.4"),
        ("1.1.7.7", "1.1.7.7"),
        ("v1.1.7.7", "1.1.7.7"),
        ("v3.28.3", "3.28.3"),
    ],
)
def test_clarified_follows_hint_for_semver(hint, expected_clarified):
    assert clarified_version_from_oss_version(hint) == expected_clarified


def test_github_archive_hint_then_clarified():
    link = "https://github.com/Kitware/CMake/archive/refs/tags/v3.28.3.tar.gz"
    hint = _oss_version_hint_from_wget_link(link, "/t/v3.28.3.tar.gz")
    assert hint == "v3.28.3"
    assert clarified_version_from_oss_version(hint) == "3.28.3"


def test_mvnrepository_url_hint_then_clarified():
    link = "https://mvnrepository.com/artifact/org.xerial.snappy/snappy-java/1.1.7.7"
    hint = _oss_version_hint_from_wget_link(link, "")
    assert hint == "1.1.7.7"
    assert clarified_version_from_oss_version(hint) == "1.1.7.7"


class _FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


def test_debian_package_heading_version_matches_checkout(monkeypatch):
    package_html = """
    <html>
      <body>
        <h1>Package: cpp (4:10.2.1-1)</h1>
        <a href="https://deb.debian.org/debian/pool/main/g/gcc-defaults/gcc-defaults_1.190.tar.xz">
          gcc-defaults_1.190.tar.xz
        </a>
      </body>
    </html>
    """

    monkeypatch.setattr(
        downloadable_url.requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse(package_html),
    )

    tarball_url, matched_version = (
        downloadable_url._resolve_debian_package_page_to_pool_tarball(
            "https://packages.debian.org/bullseye/cpp",
            "4:10.2.1-1",
        )
    )

    assert tarball_url == (
        "http://deb.debian.org/debian/pool/main/g/gcc-defaults/gcc-defaults_1.190.tar.xz"
    )
    assert matched_version == "4:10.2.1-1"


def test_debian_search_uses_package_heading_version_for_oss_version(monkeypatch):
    search_html = """
    <html>
      <body>
        <a href="/bullseye/cpp">bullseye (oldoldstable)</a>
      </body>
    </html>
    """
    package_html = """
    <html>
      <body>
        <h1>Package: cpp (4:10.2.1-1)</h1>
        <a href="https://deb.debian.org/debian/pool/main/g/gcc-defaults/gcc-defaults_1.190.tar.xz">
          gcc-defaults_1.190.tar.xz
        </a>
      </body>
    </html>
    """

    def fake_get(url, timeout=10):
        if url == "https://packages.debian.org/search?keywords=cpp":
            return _FakeResponse(search_html)
        if url == "https://packages.debian.org/bullseye/cpp":
            return _FakeResponse(package_html)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(downloadable_url.requests, "get", fake_get)

    ret, new_link, oss_name, oss_version, pkg_type = downloadable_url.get_downloadable_url(
        "https://packages.debian.org/search?keywords=cpp",
        "4:10.2.1-1",
    )

    assert ret is True
    assert new_link == (
        "http://deb.debian.org/debian/pool/main/g/gcc-defaults/gcc-defaults_1.190.tar.xz"
    )
    assert oss_name == ""
    assert oss_version == "4:10.2.1-1"
    assert pkg_type == "deb"


def test_cli_output_result_includes_downloaded_link(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    monkeypatch.setattr(
        download_module,
        "init_log",
        lambda *_args, **_kwargs: (logging.getLogger("test-download"), {}),
    )
    monkeypatch.setattr(
        download_module,
        "download_git_clone",
        lambda *_args, **_kwargs: (False, "git failed", "", "", ""),
    )
    monkeypatch.setattr(
        download_module,
        "download_wget",
        lambda *_args, **_kwargs: (
            True,
            str(tmp_path / "pkg.tar.xz"),
            "",
            "",
            "1.0.0",
            "http://deb.debian.org/debian/pool/main/p/pkg/pkg_1.0.0.tar.xz",
        ),
    )
    monkeypatch.setattr(download_module, "extract_compressed_file", lambda *_args, **_kwargs: True)

    cli_download_and_extract(
        "https://packages.debian.org/search?keywords=pkg",
        str(tmp_path / "target"),
        str(log_dir),
        output=True,
    )

    with open(log_dir / "fosslight_download_output.json", encoding="utf-8") as output_file:
        result = json.load(output_file)

    assert result["success"] is True
    assert result["link"] == "http://deb.debian.org/debian/pool/main/p/pkg/pkg_1.0.0.tar.xz"


def test_cli_output_result_uses_empty_link_on_failure(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    monkeypatch.setattr(
        download_module,
        "init_log",
        lambda *_args, **_kwargs: (logging.getLogger("test-download"), {}),
    )
    monkeypatch.setattr(
        download_module,
        "download_git_clone",
        lambda *_args, **_kwargs: (False, "git failed", "", "", ""),
    )
    monkeypatch.setattr(
        download_module,
        "download_wget",
        lambda *_args, **_kwargs: (
            True,
            str(tmp_path / "pkg.tar.xz"),
            "",
            "",
            "1.0.0",
            "http://deb.debian.org/debian/pool/main/p/pkg/pkg_1.0.0.tar.xz",
        ),
    )
    monkeypatch.setattr(download_module, "extract_compressed_file", lambda *_args, **_kwargs: False)

    cli_download_and_extract(
        "https://packages.debian.org/search?keywords=pkg",
        str(tmp_path / "target"),
        str(log_dir),
        output=True,
    )

    with open(log_dir / "fosslight_download_output.json", encoding="utf-8") as output_file:
        result = json.load(output_file)

    assert result["success"] is False
    assert result["link"] == ""
