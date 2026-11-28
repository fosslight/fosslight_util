# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""excluding_files() must keep wildcards when stripping a trailing slash."""

from pathlib import Path

from fosslight_util.exclude import excluding_files


def _tree(tmp_path: Path) -> Path:
    (tmp_path / "build_out").mkdir()
    (tmp_path / "build_out" / "a.c").write_text("int a;\n", encoding="utf-8")
    (tmp_path / "build_report.c").write_text("int r;\n", encoding="utf-8")
    return tmp_path


def test_trailing_slash_wildcard_excludes_matching_directory(tmp_path):
    root = _tree(tmp_path)
    assert excluding_files(["build*/"], str(root)) == ["build_out/a.c"]


def test_trailing_slash_star_wildcard_excludes_matching_directory(tmp_path):
    root = _tree(tmp_path)
    assert excluding_files(["build*/*"], str(root)) == ["build_out/a.c"]


def test_unslashed_wildcard_also_matches_files(tmp_path):
    root = _tree(tmp_path)
    assert excluding_files(["build*"], str(root)) == [
        "build_out/a.c",
        "build_report.c",
    ]


def test_exact_directory_slash_still_excludes_contents(tmp_path):
    root = _tree(tmp_path)
    assert excluding_files(["build_out/"], str(root)) == ["build_out/a.c"]


def test_repeated_trailing_separators_preserve_directory_patterns(tmp_path):
    root = _tree(tmp_path)
    for pattern in ["build_out//", "build*//", "build*//*"]:
        assert excluding_files([pattern], str(root)) == ["build_out/a.c"]
