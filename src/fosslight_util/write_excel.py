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
import copy
from pathlib import Path
import fosslight_util.constant as constant
from jsonmerge import merge

_HEADER = {'BIN (': ['ID', 'Binary Name', 'Source Code Path',
                     'NOTICE.html', 'OSS Name', 'OSS Version',
                     'License', 'Download Location', 'Homepage',
                     'Copyright Text', 'Exclude', 'Comment'],
           'SRC': ['ID', 'Source Name or Path', 'OSS Name',
                   'OSS Version', 'License',  'Download Location',
                   'Homepage', 'Copyright Text', 'Exclude',
                   'Comment'],
           'BIN': ['ID', 'Binary Name', 'OSS Name', 'OSS Version',
                   'License', 'Download Location', 'Homepage',
                   'Copyright Text', 'Exclude', 'Comment']}
_OUTPUT_FILE_PREFIX = "FOSSLight-Report_"
_EMPTY_ITEM_MSG = "* There is no item"\
                    " to print in FOSSLight-Report.\n"
logger = logging.getLogger(constant.LOGGER_NAME)


def write_excel_and_csv(filename_without_extension, sheet_list, ignore_os=False, extended_header={}):
    success = True
    error_msg = ""
    success_csv = True
    error_msg_csv = ""
    output_files = ""
    output_csv = ""

    is_not_null, sheet_list = remove_empty_sheet(sheet_list)

    if is_not_null:
        output_dir = os.path.dirname(filename_without_extension)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        success, error_msg = write_result_to_excel(f"{filename_without_extension}.xlsx", sheet_list, extended_header)

        if ignore_os or platform.system() != "Windows":
            success_csv, error_msg_csv, output_csv = write_result_to_csv(f"{filename_without_extension}.csv",
                                                                         sheet_list, True, extended_header)
        if success:
            output_files = f"{filename_without_extension}.xlsx"
        else:
            error_msg = "[Error] Writing excel:" + error_msg
        if success_csv:
            if output_csv:
                output_files = f"{output_files}, {output_csv}" if output_files else output_csv
        else:
            error_msg += "\n[Error] Writing csv:" + error_msg_csv
    else:
        success = False
        error_msg = _EMPTY_ITEM_MSG

    return (success and success_csv), error_msg, output_files


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


def get_header_row(sheet_name, sheet_content, extended_header={}):
    selected_header = []

    merged_headers = merge(_HEADER, extended_header)

    selected_header = merged_headers.get(sheet_name)
    if not selected_header:
        for header_key in merged_headers.keys():
            if sheet_name.startswith(header_key):
                selected_header = merged_headers[header_key]
                break

    if not selected_header:
        selected_header = sheet_content.pop(0)
    return selected_header, sheet_content


def write_result_to_csv(output_file, sheet_list_origin, separate_sheet=False, extended_header={}):
    success = True
    error_msg = ""
    file_extension = ".csv"
    output = ""

    try:
        sheet_list = copy.deepcopy(sheet_list_origin)
        if sheet_list:
            output_files = []
            output_dir = os.path.dirname(output_file)
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            if separate_sheet:
                filename = os.path.splitext(os.path.basename(output_file))[0]
                separate_output_file = os.path.join(output_dir, filename)

            merge_sheet = []
            for sheet_name, sheet_contents in sheet_list.items():
                row_num = 1
                header_row, sheet_content_without_header = get_header_row(sheet_name, sheet_contents[:], extended_header)

                if not separate_sheet:
                    merge_sheet.extend(sheet_content_without_header)
                    if sheet_name == list(sheet_list.keys())[-1]:
                        sheet_content_without_header = merge_sheet
                    else:
                        continue
                else:
                    output_file = separate_output_file + "_" + sheet_name + file_extension

                with open(output_file, 'w', newline='') as file:
                    writer = csv.writer(file, delimiter='\t')
                    writer.writerow(header_row)
                    for row_item in sheet_content_without_header:
                        row_item.insert(0, row_num)
                        writer.writerow(row_item)
                        row_num += 1
                output_files.append(output_file)
            if output_files:
                output = ", ".join(output_files)
    except Exception as ex:
        error_msg = str(ex)
        success = False

    return success, error_msg, output


def write_result_to_excel(out_file_name, sheet_list, extended_header={}):
    success = True
    error_msg = ""

    try:
        if sheet_list:
            output_dir = os.path.dirname(out_file_name)
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            workbook = xlsxwriter.Workbook(out_file_name)
            for sheet_name, sheet_contents in sheet_list.items():
                selected_header, sheet_content_without_header = get_header_row(sheet_name, sheet_contents[:], extended_header)
                worksheet = create_worksheet(workbook, sheet_name, selected_header)
                write_result_to_sheet(worksheet, sheet_content_without_header)
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


def create_worksheet(workbook, sheet_name, header_row):
    if len(sheet_name) > 31:
        current_time = str(time.time())
        sheet_name = current_time
    worksheet = workbook.add_worksheet(sheet_name)
    for col_num, value in enumerate(header_row):
        worksheet.write(0, col_num, value)
    return worksheet


def merge_excels(find_excel_dir, final_out):
    success = True
    msg = ""
    FIND_EXTENSION = '.xlsx'
    added_sheet_names = []
    try:
        files = os.listdir(find_excel_dir)

        if len([name for name in files if name.endswith(FIND_EXTENSION)]) > 0:
            writer = pd.ExcelWriter(final_out)

            for file in files:
                if file.endswith(FIND_EXTENSION):
                    f_short_name = os.path.splitext(
                        file)[0].replace(_OUTPUT_FILE_PREFIX, "")
                    file = os.path.join(find_excel_dir, file)
                    excel_file = pd.ExcelFile(file, engine='openpyxl')

                    for sheet_name in excel_file.sheet_names:
                        sheet_name_to_copy = f"{f_short_name}_{sheet_name}"
                        df_excel = pd.read_excel(
                            file, sheet_name=sheet_name, engine='openpyxl')
                        if sheet_name not in added_sheet_names:
                            sheet_name_to_copy = sheet_name
                        df_excel.to_excel(writer, sheet_name_to_copy,
                                          index=False)
            writer.save()
    except Exception as ex:
        msg = str(ex)
        success = False

    return success, msg
