# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os

from fosslight_util.write_opossum import write_opossum
from tests import constants


def test_opossum(scan_item):
    # given
    output_dir = os.path.join(constants.TEST_RESULT_DIR, "opossum")
    filename_with_dir = os.path.join(output_dir, "FL-TEST_opossum.json")

    # when
    success, _ = write_opossum(filename_with_dir, scan_item)

    # then
    assert success is True
    assert len(os.listdir(output_dir)) > 0
