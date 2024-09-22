# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
from fosslight_util.write_opossum import write_opossum

# legacy/test_opossum

def test_opossum(sheet_list_fixture):
    #given
    sheet_contents = sheet_list_fixture[1]
    output_dir = 'test_result/opossum'

    #when
    success, msg = write_opossum(output_dir + '/FL-TEST_opossum.json', sheet_contents)

    #then
    assert success is True
    assert len(os.listdir(output_dir)) > 0
