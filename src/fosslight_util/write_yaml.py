#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import yaml
import logging
import os
import copy
from pathlib import Path
import fosslight_util.constant as constant
from fosslight_util.oss_item import OssItem
from fosslight_util.write_excel import remove_empty_sheet, _EMPTY_ITEM_MSG

_logger = logging.getLogger(constant.LOGGER_NAME)


def write_yaml(output_file, sheet_list_origin, separate_yaml=False):
    success = True
    error_msg = ""
    output = ""

    try:
        sheet_list = copy.deepcopy(sheet_list_origin)
        is_not_null, sheet_list = remove_empty_sheet(sheet_list)
        if is_not_null:
            output_files = []
            output_dir = os.path.dirname(output_file)

            Path(output_dir).mkdir(parents=True, exist_ok=True)
            if separate_yaml:
                filename = os.path.splitext(os.path.basename(output_file))[0]
                separate_output_file = os.path.join(output_dir, filename)

            merge_sheet = []
            for sheet_name, sheet_contents in sheet_list.items():
                if sheet_name not in constant.supported_sheet_and_scanner.keys():
                    continue
                if not separate_yaml:
                    merge_sheet.extend(sheet_contents)
                else:
                    output_file = f'{separate_output_file}_{sheet_name}.yaml'
                    convert_sheet_to_yaml(sheet_contents, output_file)
                    output_files.append(output_file)

            if not separate_yaml:
                convert_sheet_to_yaml(merge_sheet, output_file)
                output_files.append(output_file)

            if output_files:
                output = ", ".join(output_files)
        else:
            success = False
            error_msg = _EMPTY_ITEM_MSG
    except Exception as ex:
        error_msg = str(ex)
        success = False

    if not success:
        error_msg = "[Error] Writing yaml:" + error_msg

    return success, error_msg, output


def convert_sheet_to_yaml(sheet_contents, output_file):
    sheet_contents = [list(t) for t in set(tuple(e) for e in sorted(sheet_contents))]
    try:
        find_val = [list(t) for t in set(tuple(e[1:8]) for e in sheet_contents)]
        find_idx = []
        for find_val_i in find_val:
            idx = 0
            find = False
            for e in sheet_contents:
                if find_val_i == e[1:8]:
                    if find:
                        find_idx.append(idx)
                    find = True
                idx += 1

        for index in sorted(find_idx, reverse=True):
            del sheet_contents[index]
    except Exception as e:
        _logger.debug(f"Fail to merge duplicated sheet: {e}")

    yaml_dict = {}
    for sheet_item in sheet_contents:
        item = OssItem('')
        item.set_sheet_item(sheet_item)
        item_json = copy.deepcopy(item.get_print_json())
        item_name = item_json.pop("name")
        if item_name not in yaml_dict.keys():
            yaml_dict[item_name] = []
        yaml_dict[item_name].append(item_json)

    with open(output_file, 'w') as f:
        yaml.dump(yaml_dict, f, default_flow_style=False, sort_keys=False)
