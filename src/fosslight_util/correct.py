#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import copy
import re
from fosslight_util.constant import LOGGER_NAME, FOSSLIGHT_SOURCE
from fosslight_util.parsing_yaml import parsing_yml

logger = logging.getLogger(LOGGER_NAME)
SBOM_INFO_YAML = r"sbom(-|_)info[\s\S]*.ya?ml"


def correct_with_yaml(correct_filepath, path_to_scan, scan_item):
    success = True
    msg = ""
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
        return success, msg, scan_item

    rel_path = os.path.relpath(path_to_scan, correct_filepath)

    yaml_file_list, _, err_msg = parsing_yml(correct_yaml, os.path.dirname(correct_yaml), print_log=True)
    find_match = False
    for scanner_name, _ in scan_item.file_items.items():
        correct_fileitems = []
        exclude_fileitems = []
        for yaml_file_item in yaml_file_list:
            yaml_path_exists = False
            if yaml_file_item.source_name_or_path == '':
                if scanner_name == FOSSLIGHT_SOURCE:
                    correct_item = copy.deepcopy(yaml_file_item)
                    correct_item.comment = 'Added by sbom-info.yaml'
                    correct_fileitems.append(correct_item)
                continue
            for idx, scan_file_item in enumerate(scan_item.file_items[scanner_name]):
                oss_rel_path = os.path.normpath(os.path.join(rel_path, scan_file_item.source_name_or_path))
                yi_path = yaml_file_item.source_name_or_path
                if ((os.path.normpath(yi_path) == os.path.normpath(oss_rel_path)) or
                   ((os.path.normpath(oss_rel_path).startswith(os.path.normpath(yi_path.rstrip('*')))))):
                    correct_item = copy.deepcopy(scan_file_item)
                    correct_item.exclude = yaml_file_item.exclude
                    correct_item.oss_items = copy.deepcopy(yaml_file_item.oss_items)
                    correct_item.comment = ''
                    correct_item.comment = 'Loaded from sbom-info.yaml'
                    correct_fileitems.append(correct_item)

                    yaml_path_exists = True
                    exclude_fileitems.append(idx)
            if scanner_name == FOSSLIGHT_SOURCE and not yaml_path_exists:
                correct_item = copy.deepcopy(yaml_file_item)
                if os.path.exists(os.path.normpath(yaml_file_item.source_name_or_path)):
                    correct_item.comment = 'Loaded from sbom-info.yaml'
                    correct_fileitems.append(correct_item)
                else:
                    correct_item.exclude = True
                    correct_item.comment = 'Added by sbom-info.yaml'
                    correct_fileitems.append(correct_item)
        if correct_fileitems:
            scan_item.append_file_items(correct_fileitems, scanner_name)
            find_match = True
        if exclude_fileitems:
            exclude_fileitems = list(set(exclude_fileitems))
            for e_idx in exclude_fileitems:
                scan_item.file_items[scanner_name][e_idx].exclude = True
                scan_item.file_items[scanner_name][e_idx].comment = 'Excluded by sbom-info.yaml'

    if not find_match:
        success = False
        err_msg = 'No match items in sbom-info.yaml'
        return success, err_msg, scan_item

    return success, msg, scan_item
