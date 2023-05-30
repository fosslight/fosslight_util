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
        correct_filepath = os.getcwd()

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
            oss_rel_path = os.path.join(rel_path, oss_item.source_name_or_path[0])
            for yi in yaml_oss_list:
                filtered_exact = next(filter(lambda ys: os.path.normpath(ys) == os.path.normpath(oss_rel_path),
                                      yi.source_name_or_path), None)
                if filtered_exact:
                    find_match = True
                    matched_yi.append(yi)
                    continue
                filtered_contain = next(filter(lambda ys:
                                        os.path.normpath(oss_rel_path).startswith(os.path.normpath(ys.rstrip('*'))),
                                        yi.source_name_or_path), None)
                if filtered_contain:
                    find_match = True
                    matched_yi.append(yi)
            if len(matched_yi) > 0:
                for mi in matched_yi:
                    matched_oss_item = copy.deepcopy(mi)
                    if oss_item.exclude:
                        matched_oss_item.exclude = oss_item.exclude
                    if matched_oss_item.comment:
                        matched_oss_item.comment += '/'
                    matched_oss_item.comment += 'Loaded from sbom-info.yaml'
                    matched_oss_item.source_name_or_path = []
                    matched_oss_item.source_name_or_path = oss_item.source_name_or_path[0]
                    matched_oss_array = matched_oss_item.get_print_array()[0]
                    correct_contents.append(matched_oss_array)
                oss_item.exclude = True
                if oss_item.comment:
                    oss_item.comment += '/'
                oss_item.comment += 'Excluded by sbom-info.yaml'
                correct_contents[idx] = oss_item.get_print_array()[0]
        correct_list[sheet_name] = correct_contents

    if not find_match:
        success = False
        err_msg = 'No match items in sbom-info.yaml'
        return success, err_msg, yaml_oss_list

    return success, msg, correct_list
