#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import yaml
import logging
import codecs
import os
import re
import sys
from fosslight_util.constant import LOGGER_NAME
from fosslight_util.oss_item import OssItem, FileItem

_logger = logging.getLogger(LOGGER_NAME)
SUPPORT_OSS_INFO_FILES = [r"oss-pkg-info[\s\S]*.ya?ml", r"sbom(-|_)info[\s\S]*.ya?ml"]
EXAMPLE_OSS_PKG_INFO_LINK = "https://github.com/fosslight/fosslight_prechecker/blob/main/tests/convert/sbom-info.yaml"


def parsing_yml(yaml_file, base_path, print_log=True):
    fileitems = []
    license_list = []
    idx = 1
    err_reason = ""
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
        # If yaml file is empty, return immediately
        if doc is None:
            err_reason = "empty"
            if print_log:
                _logger.warning(f"The yaml file is empty file: {yaml_file}")
            return fileitems, license_list, err_reason

        is_old_format = any(x in doc for x in OLD_YAML_ROOT_ELEMENT)

        filepath_list = []
        for root_element in doc:
            oss_items = doc[root_element]
            if oss_items:
                if not isinstance(oss_items, list) or 'version' not in oss_items[0]:
                    raise AttributeError(f"- Ref. {EXAMPLE_OSS_PKG_INFO_LINK}")
                for oss in oss_items:
                    source_paths = get_source_name_or_path_in_yaml(oss)
                    for source_path in source_paths:
                        if os.path.join(relative_path, source_path) not in filepath_list:
                            filepath_list.append(os.path.join(relative_path, source_path))
                            fileitem = FileItem(relative_path)
                            fileitem.source_name_or_path = source_path
                            fileitems.append(fileitem)
                        else:
                            fileitem = next((i for i in fileitems if i.source_name_or_path == source_path), None)
                        ossitem = OssItem()
                        if not is_old_format:
                            ossitem.name = root_element
                        for key, value in oss.items():
                            if key:
                                key = key.lower().strip()
                            set_value_switch(ossitem, key, value, yaml_file)
                        fileitem.oss_items.append(ossitem)
                        license_list.extend(ossitem.license)
                        idx += 1
    except AttributeError as ex:
        if print_log:
            _logger.warning(f"Not supported yaml file format: {yaml_file} {ex}")
        fileitems = []
        err_reason = "not_supported"
    except yaml.YAMLError:
        if print_log:
            _logger.warning(f"Error to parse yaml - skip to parse yaml file: {yaml_file}")
        fileitems = []
        err_reason = "yaml_error"

    return fileitems, set(license_list), err_reason


def get_source_name_or_path_in_yaml(oss):
    source_name_or_path = []
    find = False
    for key in oss.keys():
        if key in ['file name or path', 'source name or path', 'source path',
                   'file', 'binary name', 'binary path']:
            if isinstance(oss[key], list):
                source_name_or_path = oss[key]
            else:
                source_name_or_path.append(oss[key])
            find = True
            break
    if not find:
        source_name_or_path.append('')
    return source_name_or_path


def find_sbom_yaml_files(path_to_find):
    oss_pkg_files = []

    if not os.path.isdir(path_to_find):
        _logger.error(f"Can't find a path: {path_to_find}")
        sys.exit(os.EX_DATAERR)

    try:
        for root, dirs, files in os.walk(path_to_find):
            for file in files:
                file_name = file.lower()
                for oss_info in SUPPORT_OSS_INFO_FILES:
                    p = re.compile(oss_info, re.I)
                    if p.search(file_name):
                        oss_pkg_files.append(os.path.join(root, file))
    except Exception as ex:
        _logger.error(f"Error, find all oss-pkg-info files: {ex}")

    return oss_pkg_files


def set_value_switch(oss, key, value, yaml_file=""):
    if key in ['oss name', 'name']:
        oss.name = value
    elif key in ['oss version', 'version']:
        oss.version = value
    elif key in ['download location', 'source']:
        oss.download_location = value
    elif key in ['license', 'license text']:
        oss.license = value
    elif key in ['copyright text', 'copyright']:
        oss.copyright = value
    elif key == 'exclude':
        oss.exclude = value
    elif key == 'comment':
        oss.comment = value
    elif key == 'homepage':
        oss.homepage = value
    else:
        if yaml_file != "":
            _logger.debug(f"file:{yaml_file} - key:{key} cannot be parsed")
