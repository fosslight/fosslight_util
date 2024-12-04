# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os

from fosslight_util.write_cyclonedx import write_cyclonedx
from tests import constants


def test_cyclonedx(scan_item):
    # given
    output_dir = os.path.join(constants.TEST_RESULT_DIR, "cyclonedx")
    filename_with_dir = os.path.join(output_dir, "FL-TEST_cyclonedx.json")

    # when
    success, err_msg, _ = write_cyclonedx(filename_with_dir.split('.')[0], '.json', scan_item)

    # then
    assert success is True
    assert len(os.listdir(output_dir)) > 0
