#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import sys
from fosslight_util.output_format import write_output_file
from fosslight_util.set_log import init_log
from fosslight_util.oss_item import ScannerItem, FileItem, OssItem
from fosslight_util.constant import FOSSLIGHT_SOURCE


def main():
    logger, _result_log = init_log("test_result/output_format/log_write_output.txt")

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

    logger.warning("TESTING - Writing an excel output")
    success, msg, result_file = write_output_file(
        'test_result/output_format/FL-TEST_Excel', '.xlsx', scan_item)
    logger.warning(f"Result: {success} error_msg:: {msg}, result_file: {result_file}")

    if not success:
        sys.exit(1)

    logger.warning("TESTING - Writing an opossum output")
    success, msg, result_file = write_output_file(
        'test_result/output_format/FL-TEST_opossum', '.json', scan_item)
    logger.warning(f"Result: {success} error_msg:: {msg}, result_file: {result_file}")

    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
