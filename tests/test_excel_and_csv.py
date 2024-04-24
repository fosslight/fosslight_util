#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.write_excel import write_excel_and_csv
from fosslight_util.output_format import write_output_file
from fosslight_util.set_log import init_log
from copy import deepcopy


def main():
    logger, _result_log = init_log("test_result/excel_and_csv/log_write_excel_and_csv.txt")

    sheet_contents = {}
    src_sheet_items = [['run_scancode.py', 'fosslight_source',
                        '3.0.6', 'Apache-2.0',  'https://github.com/LGE-OSS/fosslight_source',
                        'https://github.com/LGE-OSS/fosslight_source',
                        'Copyright (c) 2021 LG Electronics, Inc.',
                        'Exclude', 'Comment message'],
                       ['', 'Enact',
                        '', 'Apache-2.0',  'https://github.com/enactjs/enact',
                        'https://enactjs.com', 'Copyright (c) 2012-2021 LG Electronics',
                        '', ''],
                       ['dependency_unified.py', 'fosslight_dependency',
                        '3.0.6', 'Apache-2.0',  'https://github.com/LGE-OSS/fosslight_dependency',
                        'https://github.com/LGE-OSS/fosslight_dependency',
                        'Copyright (c) 2020 LG Electronics, Inc.',
                        '', '']]

    bin_sheet_items = [['dependency_unified.py', 'fosslight_dependency',
                        '3.0.6', 'Apache-2.0',  'https://github.com/LGE-OSS/fosslight_dependency',
                        'https://github.com/LGE-OSS/fosslight_dependency', 'Copyright (c) 2020 LG Electronics, Inc.',
                        '', 'Awesome Open Source'],
                       ['askalono.exe', 'askalono',
                        '0.4.3', 'Apache-2.0',  'https://github.com/jpeddicord/askalono',
                        '', 'Copyright (c) 2018 Amazon.com, Inc. or its affiliates.',
                        '', '']]
    sheet_items = [['ID', 'Binary Name', 'OSS Name', 'OSS Version',
                    'License', 'Download Location', 'Homepage',
                    'Copyright Text', 'Exclude', 'Comment'],
                   ['dependency_unified.py', 'fosslight_dependency',
                    '3.0.6', 'Apache-2.0',  'https://github.com/LGE-OSS/fosslight_dependency',
                    'https://github.com/LGE-OSS/fosslight_dependency', 'Copyright (c) 2020 LG Electronics, Inc.',
                    'Exclude', 'Awesome Open Source'],
                   ['askalono.exe', 'askalono',
                    '0.4.3', 'Apache-2.0',  'https://github.com/jpeddicord/askalono',
                    '', 'Copyright (c) 2018 Amazon.com, Inc. or its affiliates.',
                    '', '']]

    sheet_contents['SRC'] = src_sheet_items
    sheet_contents['BIN_TEST'] = bin_sheet_items
    sheet_contents['SRC_NULL'] = []
    sheet_contents['CUSTOM_HEADER_SHEET'] = sheet_items

    logger.warning("TESTING - Writing an excel and csv")
    success, msg, result_file = write_excel_and_csv(
        'test_result/excel_and_csv/FOSSLight-Report', deepcopy(sheet_contents))
    logger.warning(f"|-- Result:{success}, file:{result_file}, error_msg:{msg}")

    logger.warning("TESTING - Writing an excel")
    success, msg, result_file = write_output_file('test_result/excel_and_csv/excel/Test_Excel', '.xlsx', deepcopy(sheet_contents))
    logger.warning(f"|-- Result:{success}, file:{result_file}, error_msg:{msg}")

    logger.warning("TESTING - Writing an csv")
    success, msg, result_file = write_output_file(
        'test_result/excel_and_csv/csv/Test_Csv', '.csv', deepcopy(sheet_contents))
    logger.warning(f"|-- Result:{success}, file:{result_file}, error_msg:{msg}")


if __name__ == '__main__':
    main()
