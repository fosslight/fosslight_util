#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import pytest

from fosslight_util.exclude import get_excluded_paths


@pytest.fixture
def project(tmp_path):
    for name in (
        "build_out/a.c", "pkg/build_out/nested.c", "pkg/build_out/deeper/deep.c",
        "sample/b.c", "pkg/sample/nested.c", "src/c.c",
        "build_report.c", "pkg/build_report.c", "sample.c",
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("int example;\n", encoding="utf-8")
    return str(tmp_path)


@pytest.mark.parametrize("pattern", ["build*/", "build*//", "build*/*", "build*\\"])
def test_directory_wildcard_excludes_top_level_and_nested_directories(project, pattern):
    paths, visible_paths, files, count = get_excluded_paths(project, custom_excluded_paths=[pattern])

    assert set(paths) == {"build_out", "pkg/build_out"}
    assert set(visible_paths) == {"build_out", "pkg/build_out"}
    assert set(files) == {"build_out/a.c", "pkg/build_out/nested.c", "pkg/build_out/deeper/deep.c"}
    # Directory-only patterns leave both build_report.c files available to scan.
    assert count == 6


@pytest.mark.parametrize("pattern", ["sample/", "sample//", "sample/*", "sample"])
def test_plain_directory_excludes_top_level_and_nested_directories(project, pattern):
    paths, visible_paths, files, count = get_excluded_paths(project, custom_excluded_paths=[pattern])

    assert set(paths) == {"sample", "pkg/sample"}
    assert set(visible_paths) == {"sample", "pkg/sample"}
    assert set(files) == {"sample/b.c", "pkg/sample/nested.c"}
    assert count == 7


def test_general_wildcard_also_excludes_matching_files(project):
    paths, visible_paths, files, count = get_excluded_paths(project, custom_excluded_paths=["build*"])

    assert set(paths) == {"build_out", "pkg/build_out", "build_report.c", "pkg/build_report.c"}
    assert set(visible_paths) == set(paths)
    assert set(files) == {
        "build_out/a.c", "pkg/build_out/nested.c", "pkg/build_out/deeper/deep.c",
        "build_report.c", "pkg/build_report.c",
    }
    assert count == 4


@pytest.mark.parametrize("pattern", ["pkg/build*/", "pkg/build*//", "pkg/build*/*"])
def test_relative_directory_pattern_does_not_exclude_top_level_match(project, pattern):
    paths, visible_paths, files, count = get_excluded_paths(project, custom_excluded_paths=[pattern])

    assert paths == ["pkg/build_out"]
    assert visible_paths == ["pkg/build_out"]
    assert set(files) == {"pkg/build_out/nested.c", "pkg/build_out/deeper/deep.c"}
    assert count == 7


def test_literal_directory_name_with_glob_characters(tmp_path):
    path = tmp_path / "a[1]" / "x.c"
    path.parent.mkdir()
    path.write_text("int example;\n", encoding="utf-8")

    paths, _, files, _ = get_excluded_paths(str(tmp_path), custom_excluded_paths=["a[1]/"])

    assert paths == ["a[1]"]
    assert files == ["a[1]/x.c"]
