# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
from copy import deepcopy

import openpyxl
import pytest

from fosslight_util.output_format import write_output_file


@pytest.mark.parametrize("sheet_name, expected_state", [
    (".test_hidden", "hidden"),
    ("visible_sheet", "visible"),
])
def test_external_sheet_visibility(sheet_name, expected_state, scan_item):
    output_dir = "test_result/excel_and_csv/excel"
    os.makedirs(output_dir, exist_ok=True)
    output_file_without_extension = os.path.join(output_dir, f"Test_{sheet_name.lstrip('.')}")

    scan_item.external_sheets[sheet_name] = [["Col"], ["val"]]

    success, _, result_file = write_output_file(
        output_file_without_extension, ".xlsx", deepcopy(scan_item)
    )

    assert success is True
    workbook = openpyxl.load_workbook(result_file)
    assert workbook[sheet_name].sheet_state == expected_state
