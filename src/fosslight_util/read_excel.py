#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import List, Dict, Any
import pandas as pd
import json
from fosslight_util.constant import LOGGER_NAME
from fosslight_util.oss_item import OssItem
from fosslight_util.parsing_yaml import set_value_switch

logger = logging.getLogger(LOGGER_NAME)
IDX_CANNOT_FOUND = -1
PREFIX_BIN = "bin"
SHEET_PREFIX_TO_READ = ["bin", "bom", "src"]


def read_oss_report(excel_file: str, sheet_names: str = "") -> List[OssItem]:
    oss_report_items: List[OssItem] = []
    xl_sheets: Dict[str, Any] = {}
    all_sheet_to_read: List[str] = []
    not_matched_sheet: List[str] = []
    any_sheet_matched = False
    if sheet_names:
        sheet_name_prefix_match = False
        sheet_name_to_read = sheet_names.split(",")
    else:
        sheet_name_prefix_match = True
        sheet_name_to_read = SHEET_PREFIX_TO_READ

    if True:
        logger.info(f"Read data from : {excel_file}")
        xl_workbook = pd.ExcelFile(excel_file, engine='openpyxl')
        all_sheet_in_excel = xl_workbook.sheet_names
        for sheet_to_read in sheet_name_to_read:
            try:
                any_sheet_matched = False
                sheet_to_read_lower = sheet_to_read.lower()
                all_sheet_to_read.append(sheet_to_read_lower)
                for sheet_name in all_sheet_in_excel:
                    sheet_name_lower = sheet_name.lower()
                    if (sheet_name_prefix_match and sheet_name_lower.startswith(sheet_to_read_lower)) \
                       or sheet_to_read_lower == sheet_name_lower:
                        sheet = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl', na_values='')
                        xl_sheets[sheet_name] = sheet.fillna('')
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

        for sheet_name, xl_sheet in xl_sheets.items():
            _item_idx = {
                "ID": IDX_CANNOT_FOUND,
                "Source Name or Path": IDX_CANNOT_FOUND,
                "Source Path": IDX_CANNOT_FOUND,
                "Binary Name": IDX_CANNOT_FOUND,
                "Binary Path": IDX_CANNOT_FOUND,
                "OSS Name": IDX_CANNOT_FOUND,
                "OSS Version": IDX_CANNOT_FOUND,
                "License": IDX_CANNOT_FOUND,
                "Download Location": IDX_CANNOT_FOUND,
                "Homepage": IDX_CANNOT_FOUND,
                "Exclude": IDX_CANNOT_FOUND,
                "Copyright Text": IDX_CANNOT_FOUND,
                "Comment": IDX_CANNOT_FOUND,
                "File Name or Path": IDX_CANNOT_FOUND,
                "Vulnerability Link": IDX_CANNOT_FOUND,
                "TLSH": IDX_CANNOT_FOUND,
                "SHA1": IDX_CANNOT_FOUND
            }

            for index, value in enumerate(xl_sheet.columns.tolist()):
                _item_idx[value] = index

            # Get all values, iterating through rows and columns
            column_keys = json.loads(json.dumps(_item_idx))

            is_bin = True if sheet_name.lower().startswith(PREFIX_BIN) else False

            for row_idx, row in xl_sheet.iterrows():
                item = OssItem("")
                item.is_binary = is_bin
                valid_row = True
                load_data_cnt = 0

                for column_key, column_idx in column_keys.items():
                    if column_idx != IDX_CANNOT_FOUND:
                        cell_obj = xl_sheet.iloc[row_idx, column_idx]
                        cell_value = cell_obj

                        if cell_value != "":
                            if column_key != "ID":
                                if column_key:
                                    column_key = column_key.lower().strip()
                                set_value_switch(item, column_key, cell_value)
                                load_data_cnt += 1
                            else:
                                valid_row = False if cell_value == "-" else True
                if valid_row and load_data_cnt > 0:
                    oss_report_items.append(item)

    return oss_report_items
