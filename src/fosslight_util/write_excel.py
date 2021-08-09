#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import xlsxwriter
import csv
import time
import logging
import os
import platform
import pandas as pd
from pathlib import Path
import fosslight_util.constant as constant

_HEADER = {'SRC': ['ID', 'Source Name or Path', 'OSS Name',
                   'OSS Version', 'License',  'Download Location',
                   'Homepage', 'Copyright Text', 'Exclude',
                   'Comment'],
           'BIN': ['ID', 'Binary Name', 'OSS Name', 'OSS Version',
                   'License', 'Download Location', 'Homepage',
                   'Copyright Text', 'Exclude', 'Comment'],
           'BIN (Android)': ['ID', 'Binary Name', 'Source Code Path',
                             'NOTICE.html', 'OSS Name', 'OSS Version',
                             'License', 'Download Location', 'Homepage',
                             'Copyright Text', 'Exclude', 'Comment']}
_OUTPUT_FILE_PREFIX = "FOSSLight-Report_"
_EMPTY_ITEM_MSG = "* There is no item"\
                    " to print in FOSSLight-Report.\n"
logger = logging.getLogger(constant.LOGGER_NAME)


def write_excel_and_csv(filename_without_extension, sheet_list, ignore_os=False):
    # sheet_list = {} // Key = Sheet_name, Value = list of [row_items]
    success = True
    error_msg = ""
    success_csv = True
    error_msg_csv = ""

    is_not_null, sheet_list = remove_empty_sheet(sheet_list)

    if is_not_null:
        output_dir = os.path.dirname(filename_without_extension)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        success, error_msg = write_result_to_excel(filename_without_extension + ".xlsx", sheet_list)

        if ignore_os or platform.system() != "Windows":
            success_csv, error_msg_csv = write_result_to_csv(filename_without_extension + ".csv", sheet_list)
        if not success:
            error_msg = "[Error] Writing excel:" + error_msg
        if not success_csv:
            error_msg += "\n[Error] Writing csv:" + error_msg_csv
    else:
        success = False
        error_msg = _EMPTY_ITEM_MSG

    return (success and success_csv), error_msg


def remove_empty_sheet(sheet_items):
    skip_sheet_name = []
    cnt_sheet_to_print = 0
    final_sheet_to_print = {}
    success = False

    try:
        if sheet_items:
            for sheet_name, sheet_content in sheet_items.items():
                logger.debug("ITEM COUNT:" + str(len(sheet_content)))
                if len(sheet_content) > 0:
                    final_sheet_to_print[sheet_name] = sheet_content
                    cnt_sheet_to_print += 1
                else:
                    skip_sheet_name.append(sheet_name)
            if cnt_sheet_to_print != 0:
                success = True
                if len(skip_sheet_name) > 0:
                    logger.warn("* Empty sheet(not printed):" + str(skip_sheet_name))
    except Exception as ex:
        logger.warn("* Warning:"+str(ex))

    return success, final_sheet_to_print


def write_result_to_csv(output_file, sheet_list):
    success = True
    error_msg = ""
    _header_added = False
    try:
        row_num = 1
        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file, delimiter='\t')

            for sheet_name, sheet_contents in sheet_list.items():
                if not _header_added:  # Write a header row only once
                    for header_key in _HEADER.keys():
                        if header_key in sheet_name:
                            writer.writerow(_HEADER[header_key])
                            _header_added = True
                            break
                for row_item in sheet_contents:
                    row_item.insert(0, row_num)
                    writer.writerow(row_item)
                    row_num += 1
    except Exception as ex:
        error_msg = str(ex)
        success = False
    return success, error_msg


def write_result_to_excel(out_file_name, sheet_list):
    success = True
    error_msg = ""
    try:
        workbook = xlsxwriter.Workbook(out_file_name)
        for sheet_name, sheet_contents in sheet_list.items():
            selected_header = ""
            for header_key in _HEADER.keys():
                if header_key in sheet_name:
                    selected_header = header_key
                    break
            worksheet = create_worksheet(workbook, sheet_name, selected_header)
            write_result_to_sheet(worksheet, sheet_contents)
        workbook.close()
    except Exception as ex:
        error_msg = str(ex)
        success = False
    return success, error_msg


def write_result_to_sheet(worksheet, sheet_contents):
    row = 1
    for row_item in sheet_contents:
        worksheet.write(row, 0, row)
        for col_num, value in enumerate(row_item):
            worksheet.write(row, col_num + 1, value)
        row += 1


def create_worksheet(workbook, sheet_name, header_key):
    if len(sheet_name) > 31:
        current_time = str(time.time())
        sheet_name = current_time
    worksheet = workbook.add_worksheet(sheet_name)
    if header_key in _HEADER:
        for col_num, value in enumerate(_HEADER[header_key]):
            worksheet.write(0, col_num, value)
    return worksheet


def merge_excels(find_excel_dir, final_out):
    success = True
    error_msg = ""
    _find_extension = '.xlsx'

    try:
        files = os.listdir(find_excel_dir)

        if len([name for name in files if name.endswith(_find_extension)]) > 0:
            writer = pd.ExcelWriter(final_out)

            for file in files:
                if file.endswith(_find_extension):
                    f_short_name = os.path.splitext(
                        file)[0].replace(_OUTPUT_FILE_PREFIX, "")
                    file = os.path.join(find_excel_dir, file)
                    excel_file = pd.ExcelFile(file, engine='openpyxl')

                    for sheet_name in excel_file.sheet_names:
                        df_excel = pd.read_excel(
                            file, sheet_name=sheet_name, engine='openpyxl')
                        df_excel.to_excel(
                            writer, f_short_name + '_' + sheet_name,
                            index=False)
            writer.save()
    except Exception as ex:
        error_msg = str(ex)
        success = False
    return success, error_msg
