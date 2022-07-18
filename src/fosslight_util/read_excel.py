#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import xlrd
import json
from fosslight_util.constant import LOGGER_NAME
from fosslight_util.oss_item import OssItem
from fosslight_util.parsing_yaml import set_value_switch

logger = logging.getLogger(LOGGER_NAME)
IDX_CANNOT_FOUND = -1


def read_oss_report(excel_file, sheet_names=""):
    _oss_report_items = []
    _xl_sheets = []
    all_sheet_to_read = []
    not_matched_sheet = []
    any_sheet_matched = False
    SHEET_PREFIX_TO_READ = ["bin", "bom", "src"]
    if sheet_names:
        sheet_name_prefix_match = False
        sheet_name_to_read = sheet_names.split(",")
    else:
        sheet_name_prefix_match = True
        sheet_name_to_read = SHEET_PREFIX_TO_READ

    try:
        logger.info(f"Read data from : {excel_file}")
        xl_workbook = xlrd.open_workbook(excel_file)
        all_sheet_in_excel = xl_workbook.sheet_names()

        for sheet_to_read in sheet_name_to_read:
            try:
                any_sheet_matched = False
                sheet_to_read_lower = sheet_to_read.lower()
                all_sheet_to_read.append(sheet_to_read_lower)
                for sheet_name in all_sheet_in_excel:
                    sheet_name_lower = sheet_name.lower()
                    if (sheet_name_prefix_match and sheet_name_lower.startswith(sheet_to_read_lower)) \
                       or sheet_to_read_lower == sheet_name_lower:
                        sheet = xl_workbook.sheet_by_name(sheet_name)
                        if sheet:
                            logger.info(f"Load a matched sheet: {sheet_name}")
                            _xl_sheets.append(sheet)
                            any_sheet_matched = True
                if not any_sheet_matched:
                    not_matched_sheet.append(sheet_to_read)
            except Exception as error:
                logger.debug(f"Failed to load sheet: {sheet_name} {error}")

        # Not matched any sheet
        if len(sheet_name_to_read) == len(not_matched_sheet):
            logger.warning("No sheet names are matched.")
        # Partially matched
        elif (not sheet_name_prefix_match) and not_matched_sheet:
            logger.warning(f"Not matched sheet name: {not_matched_sheet}")

        for xl_sheet in _xl_sheets:
            _item_idx = {
                "ID": IDX_CANNOT_FOUND,
                "Source Name or Path": IDX_CANNOT_FOUND,
                "Binary Name": IDX_CANNOT_FOUND,
                "OSS Name": IDX_CANNOT_FOUND,
                "OSS Version": IDX_CANNOT_FOUND,
                "License": IDX_CANNOT_FOUND,
                "Download Location": IDX_CANNOT_FOUND,
                "Homepage": IDX_CANNOT_FOUND,
                "Exclude": IDX_CANNOT_FOUND,
                "Copyright Text": IDX_CANNOT_FOUND,
                "Comment": IDX_CANNOT_FOUND,
                "File Name or Path": IDX_CANNOT_FOUND
            }
            num_cols = xl_sheet.ncols
            num_rows = xl_sheet.nrows
            MAX_FIND_HEADER_COLUMN = 5 if num_rows > 5 else num_rows
            DATA_START_ROW_IDX = 1
            for row_idx in range(0, MAX_FIND_HEADER_COLUMN):
                for col_idx in range(row_idx, num_cols):
                    cell_obj = xl_sheet.cell(row_idx, col_idx)
                    if cell_obj.value in _item_idx:
                        _item_idx[cell_obj.value] = col_idx

                if len([key for key, value in _item_idx.items() if value != IDX_CANNOT_FOUND]) > 3:
                    DATA_START_ROW_IDX = row_idx + 1
                    break

            # Get all values, iterating through rows and columns
            column_keys = json.loads(json.dumps(_item_idx))

            for row_idx in range(DATA_START_ROW_IDX, xl_sheet.nrows):
                item = OssItem("")
                valid_row = True
                load_data_cnt = 0

                for column_key, column_idx in column_keys.items():
                    if column_idx != IDX_CANNOT_FOUND:
                        cell_obj = xl_sheet.cell(row_idx, column_idx)
                        cell_value = cell_obj.value
                        if cell_value != "":
                            if column_key != "ID":
                                if column_key:
                                    column_key = column_key.lower().strip()
                                set_value_switch(item, column_key, cell_value)
                                load_data_cnt += 1
                            else:
                                valid_row = False if cell_value == "-" else True
                if valid_row and load_data_cnt > 0:
                    _oss_report_items.append(item)

    except Exception as error:
        logger.error(f"Parsing a OSS Report: {error}")
    return _oss_report_items
