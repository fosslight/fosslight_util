# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
from tests import constants
from fosslight_util.convert_excel_to_yaml import convert_excel_to_yaml

# legacy/test_convert_to_yaml

def test_convert_excel_to_yaml():
    #given
    excel_file_to_read = os.path.join(constants.TEST_RESOURCES_DIR, "FOSSLight-Report_sample.xlsx")
    output_dir = os.path.join(constants.TEST_RESULT_DIR, "convert")
    output_yaml = os.path.join(os.path.abspath(output_dir), "fosslight-sbom-info")

    #when
    convert_excel_to_yaml(excel_file_to_read, output_yaml)

    #then
    assert len(os.listdir(output_dir)) > 0
