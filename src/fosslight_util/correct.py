#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import copy
from fosslight_util.constant import LOGGER_NAME
from fosslight_util.parsing_yaml import parsing_yml
import fosslight_util.constant as constant
from fosslight_util.oss_item import OssItem

logger = logging.getLogger(LOGGER_NAME)
SBOM_INFO_YAML = 'sbom-info.yaml'


def correct_with_yaml(correct_filepath, path_to_scan, scanner_oss_list):
    success = True
    msg = ""
    correct_list = {}
    if correct_filepath == "":
        correct_filepath = os.getcwd()
    
    correct_yaml = os.path.join(correct_filepath, SBOM_INFO_YAML)
    if not os.path.exists(correct_yaml):
        msg = f"Cannot find {SBOM_INFO_YAML} in {correct_filepath}."
        success = False
        return success, msg, correct_list

    rel_path = os.path.relpath(path_to_scan, correct_filepath)

    yaml_oss_list, _, err_msg = parsing_yml(correct_yaml, os.path.dirname(correct_yaml), print_log=True)

    for sheet_name, sheet_contents in scanner_oss_list.items():
        if sheet_name not in constant.supported_sheet_and_scanner.keys():
            continue
        correct_contents = copy.deepcopy(sheet_contents)
        for idx, oss_raw_item in enumerate(sheet_contents):
            if len(oss_raw_item) < 9:
                logger.warning(f"sheet list is too short ({len(oss_raw_item)}): {oss_raw_item}")
                continue
            oss_item = OssItem('')
            oss_item.set_sheet_item(oss_raw_item)
            matched_yi = []
            for yi in yaml_oss_list:
                filtered_exact = next(filter(lambda ys: os.path.normpath(ys)==os.path.normpath(os.path.join(rel_path, oss_item.source_name_or_path[0])),
                                yi.source_name_or_path), None)
                if filtered_exact:
                    print('Exact match find!!')
                    matched_yi.append(yi)
                    continue
                filtered_contain = next(filter(lambda ys: os.path.normpath(os.path.join(rel_path, oss_item.source_name_or_path[0])).startswith(os.path.normpath(ys)), yi.source_name_or_path), None)
                if filtered_contain:
                    print('Contain match find!!')
                    matched_yi.append(yi)
            if len(matched_yi) > 0:
                correct_contents.remove(oss_raw_item)
                for mi in matched_yi:
                    if ','.join(sorted(mi.license)).casefold() != ','.join(sorted(oss_item.license)).casefold():
                        if mi.comment != "":
                            mi.comment += " ,"
                        mi.comment += f'scanner license:{"".join(oss_item.license)}'
                    matched_yaml_item = mi.get_print_array()[0]
                    matched_yaml_item[0] = oss_item.source_name_or_path[0]
                    print(matched_yaml_item)
                    correct_contents.append(matched_yaml_item)
                    
        correct_list[sheet_name] = correct_contents
    if yaml_oss_list == []:
        success = False
        return success, err_msg, yaml_oss_list
    
    print(success)
    print(correct_list)
    return success, msg, correct_list
