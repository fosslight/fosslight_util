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
from fosslight_util.write_excel import _EMPTY_ITEM_MSG

_logger = logging.getLogger(constant.LOGGER_NAME)


def write_yaml(output_file, sheet_list_origin, separate_yaml=False):
    success = True
    error_msg = ""
    output = ""

    try:
        sheet_list = copy.deepcopy(sheet_list_origin)
        if sheet_list:
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

    yaml_dict = {}
    for sheet_item in sheet_contents:
        item = OssItem('')
        item.set_sheet_item(sheet_item)
        create_yaml_with_ossitem(item, yaml_dict)

    with open(output_file, 'w') as f:
        yaml.dump(yaml_dict, f, default_flow_style=False, sort_keys=False)


def create_yaml_with_ossitem(item, yaml_dict):
    item_json = item.get_print_json()

    item_name = item_json.pop("name")
    if item_name not in yaml_dict.keys():
        yaml_dict[item_name] = []
    merged = False
    for oss_info in yaml_dict[item_name]:
        if oss_info.get('version', '') == item.version and \
           oss_info.get('license', []) == item.license and \
           oss_info.get('copyright text', '') == item.copyright and \
           oss_info.get('homepage', '') == item.homepage and \
           oss_info.get('download location', '') == item.download_location and \
           oss_info.get('exclude', False) == item.exclude:
            oss_info.get('source name or path', []).extend(item.source_name_or_path)
            oss_info.pop('comment', None)
            merged = True
            break

    if not merged:
        yaml_dict[item_name].append(item_json)
