#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import xlsxwriter
import csv
import time
import logging
import os
import pandas as pd
from pathlib import Path
from fosslight_util.constant import LOGGER_NAME, SHEET_NAME_FOR_SCANNER, FOSSLIGHT_BINARY
from jsonmerge import merge

_HEADER = {'BIN (': ['ID', 'Binary Path', 'Source Code Path',
                     'NOTICE.html', 'OSS Name', 'OSS Version',
                     'License', 'Download Location', 'Homepage',
                     'Copyright Text', 'Exclude', 'Comment'],
           'SRC': ['ID', 'Source Path', 'OSS Name', 'OSS Version',
                   'License', 'Download Location', 'Homepage',
                   'Copyright Text', 'Exclude', 'Comment'],
           'BIN': ['ID', 'Binary Path', 'OSS Name', 'OSS Version',
                   'License', 'Download Location', 'Homepage',
                   'Copyright Text', 'Exclude', 'Comment',
                   'Vulnerability Link', 'TLSH', 'SHA1'],
           'DEP': ['ID', 'Package URL', 'OSS Name', 'OSS Version',
                   'License', 'Download Location', 'Homepage',
                   'Copyright Text', 'Exclude', 'Comment',
                   'Depends On']}

BIN_HIDE_HEADER = {'TLSH', "SHA1"}
_OUTPUT_FILE_PREFIX = "FOSSLight-Report_"
IDX_FILE = 0
IDX_EXCLUDE = 7
logger = logging.getLogger(LOGGER_NAME)
COVER_SHEET_NAME = 'Scanner Info'
MAX_EXCEL_URL_LENGTH = 255


def get_header_row(sheet_name, extended_header={}):
    selected_header = []

    merged_headers = merge(_HEADER, extended_header)

    selected_header = merged_headers.get(sheet_name, [])
    if not selected_header:
        for header_key in merged_headers.keys():
            if sheet_name.startswith(header_key):
                selected_header = merged_headers[header_key]
                break
    return selected_header


def write_result_to_csv(output_file, scan_item, separate_sheet=False, extended_header={}):
    success = True
    error_msg = ""
    file_extension = ".csv"
    output = ""

    try:
        output_files = []
        output_dir = os.path.dirname(output_file)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        if separate_sheet:
            filename = os.path.splitext(os.path.basename(output_file))[0]
            separate_output_file = os.path.join(output_dir, filename)

        merge_sheet = []
        for scanner_name, _ in scan_item.file_items.items():
            row_num = 1
            sheet_name = ""
            if scanner_name.lower() in SHEET_NAME_FOR_SCANNER:
                sheet_name = SHEET_NAME_FOR_SCANNER[scanner_name.lower()]
            elif extended_header:
                sheet_name = list(extended_header.keys())[0]
            sheet_content_without_header = scan_item.get_print_array(scanner_name)
            header_row = get_header_row(sheet_name, extended_header)

            if 'Copyright Text' in header_row:
                idx = header_row.index('Copyright Text')-1
                for item in sheet_content_without_header:
                    item[idx] = item[idx].replace('\n', ', ')
            if not separate_sheet:
                merge_sheet.extend(sheet_content_without_header)
                if scanner_name == list(scan_item.file_items.keys())[-1]:
                    sheet_content_without_header = merge_sheet
                else:
                    continue
            else:
                output_file = separate_output_file + "_" + sheet_name + file_extension
            try:
                sheet_content_without_header = sorted(sheet_content_without_header,
                                                      key=lambda x: (x[IDX_EXCLUDE], x[IDX_FILE] == "", x[IDX_FILE]))
            except Exception:
                pass
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


def write_result_to_excel(out_file_name, scan_item, extended_header={}, hide_header={}):
    success = True
    error_msg = ""

    try:
        output_dir = os.path.dirname(out_file_name)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        workbook = xlsxwriter.Workbook(out_file_name)
        write_cover_sheet(workbook, scan_item.cover)
        if scan_item.file_items and len(scan_item.file_items.keys()) > 0:
            for scanner_name, _ in scan_item.file_items.items():
                sheet_name = ""
                if scanner_name.lower() in SHEET_NAME_FOR_SCANNER:
                    sheet_name = SHEET_NAME_FOR_SCANNER[scanner_name.lower()]
                elif extended_header:
                    sheet_name = list(extended_header.keys())[0]
                sheet_content_without_header = scan_item.get_print_array(scanner_name)
                selected_header = get_header_row(sheet_name, extended_header)
                try:
                    sheet_content_without_header = sorted(sheet_content_without_header,
                                                          key=lambda x: (x[IDX_EXCLUDE], x[IDX_FILE] == "", x[IDX_FILE]))
                except Exception:
                    pass
                if sheet_name:
                    worksheet = create_worksheet(workbook, sheet_name, selected_header)
                    write_result_to_sheet(worksheet, sheet_content_without_header)
                    if (scanner_name == FOSSLIGHT_BINARY) and (not hide_header):
                        hide_header = BIN_HIDE_HEADER
                    if hide_header:
                        hide_column(worksheet, selected_header, hide_header)

        for sheet_name, content in scan_item.external_sheets.items():
            if len(content) > 0:
                selected_header = content.pop(0)
                worksheet = create_worksheet(workbook, sheet_name, selected_header)
                write_result_to_sheet(worksheet, content)
                if hide_header:
                    hide_column(worksheet, selected_header, hide_header)

        workbook.close()
    except Exception as ex:
        error_msg = str(ex)
        success = False
    return success, error_msg


def write_cover_sheet(workbook, cover):
    worksheet = workbook.add_worksheet(COVER_SHEET_NAME)

    format_bold = workbook.add_format({'bold': True})
    worksheet.merge_range('A1:B1', 'About the scanner', format_bold)

    key_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': 'navy'})
    item_format = workbook.add_format()
    item_format.set_text_wrap()

    cover_json = cover.get_print_json()
    row = 1
    for item in cover_json:
        worksheet.write(row, 0, item, key_format)
        worksheet.write(row, 1, cover_json[item], item_format)
        row += 1
    worksheet.set_column(0, 0, 30)
    worksheet.set_column(1, 1, 100)


def write_result_to_sheet(worksheet, sheet_contents):
    row = 1
    for row_item in sheet_contents:
        worksheet.write(row, 0, row)
        for col_num, value in enumerate(row_item):
            if len(value) > MAX_EXCEL_URL_LENGTH and (value.startswith("http://") or value.startswith("https://")):
                worksheet.write_string(row, col_num + 1, str(value))
            else:
                worksheet.write(row, col_num + 1, str(value))
        row += 1


def hide_column(worksheet, selected_header, hide_header):
    for col_idx, sel_hd in enumerate(selected_header):
        for hide_hd in hide_header:
            if str(sel_hd).lower() == str(hide_hd).lower():
                worksheet.set_column(col_idx, col_idx, None, None, {"hidden": True})


def create_worksheet(workbook, sheet_name, header_row):
    if len(sheet_name) > 31:
        current_time = str(time.time())
        sheet_name = current_time
    worksheet = workbook.add_worksheet(sheet_name)
    if header_row:
        for col_num, value in enumerate(header_row):
            worksheet.write(0, col_num, value)
    return worksheet


def merge_excels(find_excel_dir, final_out, merge_files='', cover=''):
    success = True
    msg = ""
    FIND_EXTENSION = '.xlsx'
    added_sheet_names = []
    try:
        files = os.listdir(find_excel_dir)

        if len([name for name in files if name.endswith(FIND_EXTENSION)]) > 0:
            writer = pd.ExcelWriter(final_out)
            write_cover_sheet(writer.book, cover)
            for file in files:
                if merge_files:
                    if file not in merge_files:
                        continue
                if file.endswith(FIND_EXTENSION):
                    f_short_name = os.path.splitext(
                        file)[0].replace(_OUTPUT_FILE_PREFIX, "")
                    file = os.path.join(find_excel_dir, file)
                    excel_file = pd.ExcelFile(file, engine='openpyxl')

                    for sheet_name in excel_file.sheet_names:
                        if sheet_name == COVER_SHEET_NAME:
                            continue
                        df_excel = pd.read_excel(
                            file, sheet_name=sheet_name, engine='openpyxl')
                        if sheet_name in added_sheet_names:
                            sheet_name = f"{f_short_name}_{sheet_name}"
                        df_excel.to_excel(writer, sheet_name, index=False)
                        added_sheet_names.append(sheet_name)

                        if sheet_name == 'BIN_FL_Binary':
                            bin_sheet = writer.sheets[sheet_name]
                            bin_sheet.set_column("L:M", None, None, {"hidden": True})  # 'TLSH', 'SHA1' column hide
            writer.close()
    except Exception as ex:
        msg = str(ex)
        success = False

    return success, msg
