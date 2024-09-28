# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os

from fosslight_util.write_yaml import write_yaml
from tests import constants


def test_write_yaml(scan_item):
    # given
    output_dir = os.path.join(constants.TEST_RESULT_DIR, "yaml")
    output_file = os.path.join(output_dir, 'FL-TEST_yaml.yaml')

    # when
    success, _, output = write_yaml(output_file, scan_item)

    # then
    assert success is True
    assert output_file in output
