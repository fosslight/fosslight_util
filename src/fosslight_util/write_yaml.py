#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import yaml
import logging
import os
import json
from pathlib import Path
from fosslight_util.constant import LOGGER_NAME, SHEET_NAME_FOR_SCANNER
from typing import Tuple

_logger = logging.getLogger(LOGGER_NAME)


def write_yaml(output_file, scan_item, separate_yaml=False) -> Tuple[bool, str, str]:
    success = True
    error_msg = ""
    output = ""

    try:
        output_files = []
        output_dir = os.path.dirname(output_file)

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        if separate_yaml:
            filename = os.path.splitext(os.path.basename(output_file))[0]
            separate_output_file = os.path.join(output_dir, filename)

        merge_sheet = []
        for scanner_name, _ in scan_item.file_items.items():
            sheet_name = SHEET_NAME_FOR_SCANNER[scanner_name.lower()]
            json_contents = scan_item.get_print_json(scanner_name)

            if not separate_yaml:
                merge_sheet.extend(json_contents)
            else:
                output_file = f'{separate_output_file}_{sheet_name}.yaml'
                remove_duplicates_and_dump_yaml(json_contents, output_file)
                output_files.append(output_file)

        if not separate_yaml:
            remove_duplicates_and_dump_yaml(merge_sheet, output_file)
            output_files.append(output_file)

        if output_files:
            output = ", ".join(output_files)
    except Exception as ex:
        error_msg = str(ex)
        success = False

    if not success:
        error_msg = "[Error] Writing yaml:" + error_msg

    return success, error_msg, output


def remove_duplicates_and_dump_yaml(json_contents, output_file):
    unique_json_strings = {json.dumps(e, sort_keys=True) for e in json_contents}
    unique_json_contents = [json.loads(e) for e in unique_json_strings]

    yaml_dict = {}
    for uitem in unique_json_contents:
        create_yaml_with_ossitem(uitem, yaml_dict)

    with open(output_file, 'w') as f:
        yaml.dump(yaml_dict, f, default_flow_style=False, sort_keys=False)


def create_yaml_with_ossitem(item, yaml_dict):
    item_name = item.pop("name")

    if item_name not in yaml_dict.keys():
        yaml_dict[item_name] = []
    merged = False
    for oss_info in yaml_dict[item_name]:
        if oss_info.get('version', '') == item.get('version', '') and \
           oss_info.get('license', []) == item.get('license', []) and \
           oss_info.get('copyright text', '') == item.get('copyright text', '') and \
           oss_info.get('homepage', '') == item.get('homepage', '') and \
           oss_info.get('download location', '') == item.get('download location', '') and \
           oss_info.get('exclude', False) == item.get('exclude', False):
            if isinstance(oss_info.get('source path', []), str):
                oss_info['source path'] = [oss_info.get('source path', '')]
            oss_info.get('source path', []).append(item.get('source path', ''))
            oss_info.pop('comment', None)
            merged = True
            break

    if not merged:
        yaml_dict[item_name].append(item)
