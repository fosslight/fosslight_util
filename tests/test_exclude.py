#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

from fosslight_util.exclude import excluding_files


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
    assert excluding_files(["build*/*"], str(tmp_path)) == ["build_out/a.c"]


def test_trailing_slash_and_star_on_plain_directory(tmp_path):
    _make_tree(tmp_path)
    assert excluding_files(["sample/"], str(tmp_path)) == ["sample/b.c"]
    assert excluding_files(["sample/*"], str(tmp_path)) == ["sample/b.c"]
    assert excluding_files(["sample"], str(tmp_path)) == ["sample/b.c"]
