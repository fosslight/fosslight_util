#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import json
from fosslight_util.constant import LOGGER_NAME
from fosslight_util.oss_item import ScannerItem
from typing import List

logger = logging.getLogger(LOGGER_NAME)
EMPTY_FILE_PATH = '-'


def write_scancodejson(output_dir: str, output_filename: str, oss_list: List[ScannerItem]):
    json_output = {}
    json_output['headers'] = []
    json_output['summary'] = {}
    json_output['license_detections'] = []
    json_output['files'] = []

    for file_items in oss_list.file_items.values():
        for fi in file_items:
            if fi.exclude:
                continue
            if fi.oss_items and (all(oss_item.exclude for oss_item in fi.oss_items)):
                continue
            if not fi.source_name_or_path:
                fi.source_name_or_path = EMPTY_FILE_PATH
            json_output['files'] = add_item_in_files(fi, json_output['files'])

    with open(os.path.join(output_dir, output_filename), 'w') as f:
        json.dump(json_output, f, sort_keys=False, indent=4)


def append_oss_item_in_filesitem(oss_items, files_item):
    for oi in oss_items:
        if oi.exclude:
            continue
        oss_item = {}
        oss_item['name'] = oi.name
        oss_item['version'] = oi.version
        oss_item['license'] = oi.license
        oss_item['copyright'] = oi.copyright
        oss_item['download_location'] = oi.download_location
        oss_item['comment'] = oi.comment
        files_item['oss'].append(oss_item)

    return files_item


def add_item_in_files(file_item, files_list):
    files_item = {}
    files_item['path'] = file_item.source_name_or_path
    files_item['name'] = os.path.basename(file_item.source_name_or_path)
    files_item['is_binary'] = file_item.is_binary
    files_item['base_name'], files_item['extension'] = os.path.splitext(os.path.basename(file_item.source_name_or_path))
    files_item['oss'] = []
    files_item = append_oss_item_in_filesitem(file_item.oss_items, files_item)
    files_list.append(files_item)

    return files_list
