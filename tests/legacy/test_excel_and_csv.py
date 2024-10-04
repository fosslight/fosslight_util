#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.output_format import write_output_file
from fosslight_util.set_log import init_log
from copy import deepcopy
from fosslight_util.oss_item import ScannerItem, FileItem, OssItem
from fosslight_util.constant import FOSSLIGHT_SOURCE


def main():
    logger, _result_log = init_log("test_result/excel_and_csv/log_write_excel_csv.txt")

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

    logger.warning("TESTING - Writing an excel")
    success, msg, result_file = write_output_file('test_result/excel_and_csv/excel/Test_Excel', '.xlsx', deepcopy(scan_item))
    logger.warning(f"|-- Result:{success}, file:{result_file}, error_msg:{msg}")

    logger.warning("TESTING - Writing an csv")
    success, msg, result_file = write_output_file(
        'test_result/excel_and_csv/csv/Test_Csv', '.csv', deepcopy(scan_item))
    logger.warning(f"|-- Result:{success}, file:{result_file}, error_msg:{msg}")


if __name__ == '__main__':
    main()
