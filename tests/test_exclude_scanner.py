#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

"""Optional consumer integration.

Install with ``python -m pip install -e . fosslight_scanner``, then run
``python -m pytest tests/test_exclude_scanner.py``.
"""

import os
import subprocess
import sys

import openpyxl
import pytest

pytest.importorskip("fosslight_scanner", reason="Install fosslight_scanner to test the -e CLI path")


@pytest.mark.parametrize("pattern", ["build*/", "build*//", "build*/*"])
def test_scanner_cli_reports_nested_directory_exclusions(tmp_path, pattern):
    project = tmp_path / "project"
    for name in ("build_out/a.c", "pkg/build_out/deeper/b.c", "src/keep.c", "build_report.c"):
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("int example;\n", encoding="utf-8")

    report = tmp_path / "output" / "report.xlsx"
    env = os.environ.copy()
    env.update({
        "SCANCODE_CACHE": str(tmp_path / "scancode-cache"),
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
        "MPLCONFIGDIR": str(tmp_path / "matplotlib"),
    })
    # Text-only fixtures require no binary database lookup. Keep the real CLI,
    # exclusion walk, binary scanner and report writer in the integration path.
    result = subprocess.run(
        [sys.executable, "-m", "fosslight_scanner.cli", "binary",
         "-p", str(project), "-e", pattern, "-f", "excel", "-o", str(report),
         "--no_correction", "-t"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    workbook = openpyxl.load_workbook(report, read_only=True)
    try:
        info = dict(workbook["Scanner Info"].values)
        assert info["Excluded path"], "Scanner report did not record any excluded paths"
        assert set(info["Excluded path"].split(", ")) == {"build_out", "pkg/build_out"}
        assert "Scanned Files : 2" in info["Comment"]
    finally:
        workbook.close()
