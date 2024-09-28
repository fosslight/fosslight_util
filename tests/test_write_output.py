# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
from copy import deepcopy

import pytest

from fosslight_util.output_format import write_output_file


@pytest.mark.parametrize("output_dir, result_file_name, file_extension",
                         [("test_result/excel_and_csv/excel", "Test_Excel", ".xlsx"),
                          ("test_result/excel_and_csv/csv", "Test_Csv", ".csv"),
                          ("test_result/output_format", "FL-TEST_opossum", ".json")])
def test_write_excel_and_csv(output_dir, result_file_name, file_extension, scan_item):
    # given
    output_file_without_extension = os.path.join(output_dir, result_file_name)

    # when
    success, _, result_file = write_output_file(output_file_without_extension,
                                                file_extension, deepcopy(scan_item))

    # then
    assert success is True
    assert result_file_name + file_extension in result_file
