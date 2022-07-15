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
from .oss_item import OssItem

_logger = logging.getLogger(LOGGER_NAME)


def parsing_yml(yaml_file, base_path):
    oss_list = []
    license_list = []
    idx = 1
    OLD_YAML_ROOT_ELEMENT = ['Open Source Software Package',
                             'Open Source Package']

    try:
        path_of_yml = os.path.normpath(os.path.dirname(yaml_file))
        base_normpath = os.path.normpath(base_path)
        relative_path = ""
        if path_of_yml != base_normpath:
            relative_path = os.path.relpath(path_of_yml, base_normpath)
        else:
            relative_path = ""
        doc = yaml.safe_load(codecs.open(yaml_file, "r", "utf-8"))
        is_old_format = any(x in doc for x in OLD_YAML_ROOT_ELEMENT)

        for root_element in doc:
            oss_items = doc[root_element]
            if oss_items:
                for oss in oss_items:
                    item = OssItem(relative_path)
                    if not is_old_format:
                        item.name = root_element
                    for key, value in oss.items():
                        if key:
                            key = key.lower().strip()
                        set_value_switch(item, key, value)
                    oss_list.append(item)
                    license_list.extend(item.license)
                    idx += 1
    except yaml.YAMLError:
        _logger.warning(f"Can't parse yaml - skip to parse yaml file: {yaml_file}")
    return oss_list, set(license_list)


def find_all_oss_pkg_files(path_to_find, file_to_find):
    oss_pkg_files = []

    if not os.path.isdir(path_to_find):
        _logger.error(f"Can't find a path: {path_to_find}")
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
        _logger.error(f"Error, find all oss-pkg-info files: {ex}")

    return oss_pkg_files


def set_value_switch(oss, key, value):
    if key in ['oss name', 'name']:
        oss.name = value
    elif key in ['oss version', 'version']:
        oss.version = value
    elif key in ['download location', 'source']:
        oss.download_location = value
    elif key in ['license', 'license text']:
        oss.license = value
    elif key in ['file name or path', 'source name or path', 'file', 'binary name']:
        oss.source_name_or_path = value
    elif key in ['copyright text', 'copyright']:
        oss.copyright = value
    elif key == 'exclude':
        oss.exclude = value
    elif key == 'comment':
        oss.comment = value
    elif key == 'homepage':
        oss.homepage = value
