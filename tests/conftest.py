# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import shutil

import pytest

from tests import constants
from fosslight_util.constant import FOSSLIGHT_SOURCE
from fosslight_util.oss_item import ScannerItem, FileItem, OssItem

set_up_directories = [
    constants.TEST_RESULT_DIR,
    os.path.join(constants.TEST_RESULT_DIR, "convert")
]
remove_directories = [constants.TEST_RESULT_DIR]


@pytest.fixture(scope="function", autouse=True)
def setup_test_result_dir_and_teardown():
    print("==============setup==============")
    for dir in set_up_directories:
        os.makedirs(dir, exist_ok=True)

    yield

    print("==============tearDown==============")
    for dir in remove_directories:
        shutil.rmtree(dir)


@pytest.fixture
def scan_item():
    scan_item = ScannerItem(FOSSLIGHT_SOURCE)
    scan_item.set_cover_pathinfo('tests/test_excel_and_csv', '')
    scan_item.set_cover_comment('This is a test comment')

    file_item = FileItem('test_result/excel_and_csv')
    file_item.checksum = 'af969fc2085b1bb6d31e517d5c456def5cdd7093'

    oss_item = OssItem("test_name1", "1.0.0", "Apache-2.0", "https://abc.com")
    oss_item.comment = "test_name comment"
    file_item.oss_items.append(oss_item)

    oss_item2 = OssItem("test_name2", "2.0.0", "MIT", "https://abc2.com")
    file_item.oss_items.append(oss_item2)

    oss_item3 = OssItem("test_name3", "1.0.0", "GPL-2.0,BSD-3-Clause", "https://abc3.com")
    file_item.oss_items.append(oss_item3)
    file_item.comment = "all test comment"

    scan_item.append_file_items([file_item])

    return scan_item
