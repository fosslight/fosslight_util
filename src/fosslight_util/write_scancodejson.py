#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import json
import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)
EMPTY_FILE_PATH = '-'


def write_scancodejson(output_dir, output_filename, oss_list):
    json_output = {}
    json_output['headers'] = []
    json_output['summary'] = {}
    json_output['license_detections'] = []
    json_output['files'] = []

    for oi in oss_list:
        if oi.exclude:
            continue
        if not oi.source_name_or_path:
            oi.source_name_or_path = EMPTY_FILE_PATH
        for item_path in oi.source_name_or_path:
            filtered = next(filter(lambda x: x['path'] == item_path, json_output['files']), None)
            if filtered:
                append_oss_item_in_filesitem(oi, filtered)
            else:
                json_output['files'] = add_item_in_files(oi, item_path, json_output['files'])
    with open(os.path.join(output_dir, output_filename), 'w') as f:
        json.dump(json_output, f, sort_keys=False)


def append_oss_item_in_filesitem(item, files_item):
    oss_item = {}
    oss_item['name'] = item.name
    oss_item['version'] = item.version
    oss_item['license'] = item.license
    oss_item['copyright'] = item.copyright
    oss_item['download_location'] = item.download_location
    oss_item['comment'] = item.comment
    files_item['oss'].append(oss_item)
    return files_item


def add_item_in_files(item, item_path, files_list):
    files_item = {}
    files_item['path'] = item_path
    files_item['name'] = os.path.basename(item_path)
    files_item['base_name'], files_item['extension'] = os.path.splitext(os.path.basename(item_path))
    files_item['oss'] = []
    files_item = append_oss_item_in_filesitem(item, files_item)
    files_list.append(files_item)

    return files_list
