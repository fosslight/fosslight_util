# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for wget-path oss_version / clarified_version hints from URL and filename."""

import pytest

from fosslight_util.download import (
    clarified_version_from_oss_version,
    _oss_version_hint_from_wget_link,
)


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
