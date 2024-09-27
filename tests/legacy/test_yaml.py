#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.write_yaml import write_yaml
from fosslight_util.set_log import init_log
from fosslight_util.oss_item import ScannerItem, FileItem, OssItem
from fosslight_util.constant import FOSSLIGHT_SOURCE


def main():
    logger, _result_log = init_log("test_result/yaml/log_write_yaml.txt")
    logger.warning("TESTING - Writing a yaml")

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
    oss_item3 = OssItem("test_name2", "1.0.0", "GPL-2.0,BSD-3-Clause", "https://abc3.com")
    file_item.oss_items.append(oss_item3)

    scan_item.append_file_items([file_item])

    success, msg, output = write_yaml(
        'test_result/yaml/FL-TEST_yaml.yaml', scan_item)
    logger.warning(f"Result: {str(success)}, error_msg: {msg}, Output_files: {output}")


if __name__ == '__main__':
    main()
