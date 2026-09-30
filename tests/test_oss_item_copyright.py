# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

from fosslight_util.oss_item import OssItem

_COMMA = "Copyright (c) 2021 LG Electronics, Inc."
_NO_COMMA = "Copyright (c) 2021 LG Electronics Inc."


def test_copyright_string_keeps_input_order():
    comma_first = OssItem()
    comma_first.copyright = f"{_COMMA}\n{_NO_COMMA}"
    assert comma_first.copyright == f"{_COMMA}\n{_NO_COMMA}"

    plain_first = OssItem()
    plain_first.copyright = f"{_NO_COMMA}\n{_COMMA}"
    assert plain_first.copyright == f"{_NO_COMMA}\n{_COMMA}"


def test_copyright_list_keeps_input_order_and_drops_duplicates():
    item = OssItem()
    item.copyright = [_NO_COMMA, _COMMA, _NO_COMMA]

    assert item.copyright == f"{_NO_COMMA}\n{_COMMA}"
