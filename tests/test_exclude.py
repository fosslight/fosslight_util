#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

from fosslight_util.exclude import excluding_files, get_excluded_paths


def _make_tree(tmp_path):
    (tmp_path / "build_out").mkdir()
    (tmp_path / "build_out" / "a.c").write_text("")
    (tmp_path / "sample").mkdir()
    (tmp_path / "sample" / "b.c").write_text("")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "c.c").write_text("")


def test_trailing_slash_keeps_wildcard_in_directory_name(tmp_path):
    _make_tree(tmp_path)
    assert excluding_files(["build*/"], str(tmp_path)) == ["build_out/a.c"]
    assert excluding_files(["build*//"], str(tmp_path)) == ["build_out/a.c"]
    assert excluding_files(["build*/*"], str(tmp_path)) == ["build_out/a.c"]


def test_trailing_slash_and_star_on_plain_directory(tmp_path):
    _make_tree(tmp_path)
    assert excluding_files(["sample/"], str(tmp_path)) == ["sample/b.c"]
    assert excluding_files(["sample//"], str(tmp_path)) == ["sample/b.c"]
    assert excluding_files(["sample/*"], str(tmp_path)) == ["sample/b.c"]
    assert excluding_files(["sample"], str(tmp_path)) == ["sample/b.c"]


def test_get_excluded_paths_trailing_slash_wildcard(tmp_path):
    _make_tree(tmp_path)
    for pat in ["build*/", "build*//", "build*/*", "build*"]:
        _, _, excluded_files, _ = get_excluded_paths(str(tmp_path), custom_excluded_paths=[pat])
        assert sorted(excluded_files) == ["build_out/a.c"], f"failed for {pat}"


def test_get_excluded_paths_plain_directory(tmp_path):
    _make_tree(tmp_path)
    for pat in ["sample/", "sample//", "sample/*", "sample"]:
        _, _, excluded_files, _ = get_excluded_paths(str(tmp_path), custom_excluded_paths=[pat])
        assert sorted(excluded_files) == ["sample/b.c"], f"failed for {pat}"


def test_directory_only_pattern_does_not_exclude_similarly_named_files(tmp_path):
    _make_tree(tmp_path)
    (tmp_path / "build_report.c").write_text("")
    (tmp_path / "sample.c").write_text("")

    assert excluding_files(["build*/"], str(tmp_path)) == ["build_out/a.c"]
    assert excluding_files(["sample/"], str(tmp_path)) == ["sample/b.c"]
    assert excluding_files(["build*"], str(tmp_path)) == ["build_out/a.c", "build_report.c"]

    _, _, files_dir_only, _ = get_excluded_paths(str(tmp_path), custom_excluded_paths=["build*/"])
    assert sorted(files_dir_only) == ["build_out/a.c"]

    _, _, files_general, _ = get_excluded_paths(str(tmp_path), custom_excluded_paths=["build*"])
    assert sorted(files_general) == ["build_out/a.c", "build_report.c"]
