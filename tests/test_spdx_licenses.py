# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.spdx_licenses import get_spdx_licenses_json


def test_get_spdx_licenses_json():
    # when
    success, _, licenses = get_spdx_licenses_json()

    # then
    assert success is True
    assert len(licenses) > 0
