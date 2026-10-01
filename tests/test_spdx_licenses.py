# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import builtins
import os

import fosslight_util.spdx_licenses as spdx_licenses
from fosslight_util.spdx_licenses import get_spdx_licenses_json, get_license_from_nick


def test_get_spdx_licenses_json():
    # when
    success, _, licenses = get_spdx_licenses_json()

    # then
    assert success is True
    assert len(licenses) > 0


def test_resource_json_is_read_as_utf8_regardless_of_locale(monkeypatch):
    # Without an explicit encoding open() uses the locale encoding (cp949 on Korean
    # Windows), and licenses.json, which is UTF-8 with non-ASCII characters, failed to
    # load. CI runs with a UTF-8 locale, so make an unspecified encoding mean ASCII.
    real_open = builtins.open
    opened_without_encoding = []

    def open_with_non_utf8_locale(file, mode="r", *args, **kwargs):
        if "b" not in mode and "encoding" not in kwargs:
            opened_without_encoding.append(os.path.basename(file))
            kwargs["encoding"] = "ascii"
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(spdx_licenses, "open", open_with_non_utf8_locale, raising=False)

    # when
    success, error_msg, licenses = get_spdx_licenses_json()
    nicks = get_license_from_nick()

    # then
    assert success is True, error_msg
    assert len(licenses) > 0
    assert len(nicks) > 0
    assert opened_without_encoding == []
