#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import yaml
import logging
import codecs
import os
import sys
from .constant import LOGGER_NAME
from .oss_item import OssItem, invalid

_logger = logging.getLogger(LOGGER_NAME)


def parsing_yml(yaml_file, base_path):
    oss_list = []
    license_list = []
    idx = 1
    try:
        path_of_yml = os.path.normpath(os.path.dirname(yaml_file))
        base_path = os.path.normpath(base_path)
        relative_path = ""

        if path_of_yml != base_path:
            relative_path = os.path.relpath(path_of_yml, base_path)

        doc = yaml.safe_load(codecs.open(yaml_file, "r", "utf-8"))
        for root_element in doc:
            oss_items = doc[root_element]
            if oss_items:
                for oss in oss_items:
                    item = OssItem(relative_path)
                    for key, value in oss.items():
                        set_value_switch(item, key, value)
                    items_to_print = item.get_print_array()
                    for item_to_print in items_to_print:
                        item_to_print.insert(0, str(idx))
                    oss_list.extend(items_to_print)
                    license_list.extend(item.licenses)
                    idx += 1
    except yaml.YAMLError as ex:
        _logger.error('Parsing yaml :' + str(ex))
    license_list = set(license_list)
    return oss_list, license_list


def find_all_oss_pkg_files(path_to_find, file_to_find):
    oss_pkg_files = []

    if not os.path.isdir(path_to_find):
        _logger.error("Can't find a path :" + path_to_find)
        sys.exit(os.EX_DATAERR)

    try:
        # oss_pkg_files.extend(glob.glob(path_to_find + '/**/'+file, recursive=True)) #glib is too slow
        for p, d, f in os.walk(path_to_find):
            for file in f:
                file_name = file.lower()
                if file_name in file_to_find or (
                        (file_name.endswith("yml") or file_name.endswith("yaml"))
                        and file_name.startswith("oss-pkg-info")):
                    oss_pkg_files.append(os.path.join(p, file))
    except Exception as ex:
        _logger.debug("Error, find all oss-pkg-info files:" + str(ex))

    return oss_pkg_files


def set_value_switch(oss, key, value):
    switcher = {
        'name': oss.set_name,
        'version': oss.set_version,
        'source': oss.set_source,
        'license': oss.set_licenses,
        'file': oss.set_files,
        'copyright': oss.set_copyright,
        'exclude': oss.set_exclude,
        'comment': oss.set_comment,
        'homepage': oss.set_homepage
    }
    func = switcher.get(key, lambda key: invalid(key))
    func(value)
