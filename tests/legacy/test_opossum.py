#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.write_opossum import write_opossum
from fosslight_util.set_log import init_log
from fosslight_util.oss_item import ScannerItem, FileItem, OssItem
from fosslight_util.constant import FOSSLIGHT_SOURCE


def main():
    logger, _result_log = init_log("test_result/excel/log_write_opossum.txt")
    logger.warning("TESTING - Writing an opossum")

    scan_item = ScannerItem(FOSSLIGHT_SOURCE)
    scan_item.set_cover_pathinfo('tests/test_excel_and_csv', '')
    scan_item.set_cover_comment('This is a test comment')

    file_item = FileItem('test_result/excel_and_csv')
    oss_item = OssItem("test_name", "1.0.0", "Apache-2.0", "https://abc.com")
    oss_item.comment = "test_name comment"
    file_item.oss_items.append(oss_item)
    oss_item2 = OssItem("test_name", "2.0.0", "MIT", "https://abc2.com")
    file_item.oss_items.append(oss_item2)
    file_item.comment = "all test comment"

    scan_item.append_file_items([file_item])

    success, msg = write_opossum(
        'test_result/opossum/FL-TEST_opossum.json', scan_item)
    logger.warning("Result:" + str(success) + ", error_msg:" + msg)


if __name__ == '__main__':
    main()
