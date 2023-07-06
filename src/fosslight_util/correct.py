#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import copy
import re
from fosslight_util.constant import LOGGER_NAME
from fosslight_util.parsing_yaml import parsing_yml
import fosslight_util.constant as constant
from fosslight_util.oss_item import OssItem

logger = logging.getLogger(LOGGER_NAME)
SBOM_INFO_YAML = r"sbom(-|_)info[\s\S]*.ya?ml"


def correct_with_yaml(correct_filepath, path_to_scan, scanner_oss_list):
    success = True
    msg = ""
    correct_list = {}
    correct_yaml = ""
    if correct_filepath == "":
        correct_filepath = path_to_scan

    path_to_scan = os.path.normpath(path_to_scan)
    correct_filepath = os.path.normpath(correct_filepath)
    for filename in os.listdir(correct_filepath):
        if re.search(SBOM_INFO_YAML, filename, re.IGNORECASE):
            correct_yaml = os.path.join(correct_filepath, filename)
            break
    if not correct_yaml:
        msg = f"Cannot find sbom-info.yaml in {correct_filepath}."
        success = False
        return success, msg, correct_list

    rel_path = os.path.relpath(path_to_scan, correct_filepath)

    yaml_oss_list, _, err_msg = parsing_yml(correct_yaml, os.path.dirname(correct_yaml), print_log=True)

    find_match = False
    matched_yaml = []
    for yitem in yaml_oss_list:
        matched_yaml.append([0]*len(yitem.source_name_or_path))

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
            oss_rel_path = os.path.normpath(os.path.join(rel_path, oss_item.source_name_or_path[0]))
            for y_idx, yi in enumerate(yaml_oss_list):
                if not yi.source_name_or_path:
                    continue
                for ys_idx, yi_path in enumerate(yi.source_name_or_path):
                    yi_item = copy.deepcopy(yi)
                    if ((os.path.normpath(yi_path) == os.path.normpath(oss_rel_path))
                       or ((os.path.normpath(oss_rel_path).startswith(os.path.normpath(yi_path.rstrip('*')))))):
                        find_match = True
                        yi_item.source_name_or_path = []
                        yi_item.source_name_or_path = oss_item.source_name_or_path[0]
                        matched_yi.append(yi_item)
                        matched_yaml[y_idx][ys_idx] = 1
            if len(matched_yi) > 0:
                for matched_yi_item in matched_yi:
                    matched_oss_item = copy.deepcopy(matched_yi_item)
                    if matched_oss_item.comment:
                        matched_oss_item.comment += '/'
                    matched_oss_item.comment += 'Loaded from sbom-info.yaml'
                    matched_oss_array = matched_oss_item.get_print_array()[0]
                    correct_contents.append(matched_oss_array)
                oss_item.exclude = True
                if oss_item.comment:
                    oss_item.comment += '/'
                oss_item.comment += 'Excluded by sbom-info.yaml'
                correct_contents[idx] = oss_item.get_print_array()[0]

        if sheet_name == 'SRC_FL_Source':
            for n_idx, ni in enumerate(matched_yaml):
                y_item = copy.deepcopy(yaml_oss_list[n_idx])
                all_matched = False
                if sum(ni) != 0:
                    not_matched_path = []
                    for idx, id in enumerate(ni):
                        if not id:
                            not_matched_path.append(y_item.source_name_or_path[idx])
                    y_item.source_name_or_path = []
                    y_item.source_name_or_path = not_matched_path
                    if len(not_matched_path) == 0:
                        all_matched = True
                if y_item.comment:
                    y_item.comment += '/'
                y_item.comment += 'Added by sbom-info.yaml'
                if not (y_item.source_name_or_path or all_matched):
                    correct_contents.append(y_item.get_print_array()[0])
                    continue
                for y_path in y_item.source_name_or_path:
                    y_item_i = copy.deepcopy(y_item)
                    if not os.path.exists(os.path.normpath(os.path.join(correct_filepath, y_path))):
                        y_item_i.exclude = True
                    y_item_i.source_name_or_path = []
                    y_item_i.source_name_or_path = y_path
                    correct_contents.append(y_item_i.get_print_array()[0])
        correct_list[sheet_name] = correct_contents

    if not find_match:
        success = False
        err_msg = 'No match items in sbom-info.yaml'
        return success, err_msg, yaml_oss_list

    return success, msg, correct_list
