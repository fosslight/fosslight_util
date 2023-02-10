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
from .constant import LOGGER_NAME
from .oss_item import OssItem

_logger = logging.getLogger(LOGGER_NAME)
SUPPORT_OSS_INFO_FILES = [r"oss-pkg-info[\s\S]*.ya?ml", r"sbom(-|_)info[\s\S]*.ya?ml"]
EXAMPLE_OSS_PKG_INFO_LINK = "https://github.com/fosslight/fosslight_prechecker/blob/main/tests/convert/sbom-info.yaml"


def parsing_yml(yaml_file, base_path, print_log=True):
    oss_list = []
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
            return oss_list, license_list, err_reason

        is_old_format = any(x in doc for x in OLD_YAML_ROOT_ELEMENT)

        for root_element in doc:
            oss_items = doc[root_element]
            if oss_items:
                if not isinstance(oss_items, list) or 'version' not in oss_items[0]:
                    raise AttributeError(f"- Ref. {EXAMPLE_OSS_PKG_INFO_LINK}")
                for oss in oss_items:
                    item = OssItem(relative_path)
                    if not is_old_format:
                        item.name = root_element
                    for key, value in oss.items():
                        if key:
                            key = key.lower().strip()
                        set_value_switch(item, key, value, yaml_file)
                    oss_list.append(item)
                    license_list.extend(item.license)
                    idx += 1
    except AttributeError as ex:
        if print_log:
            _logger.warning(f"Not supported yaml file format: {yaml_file} {ex}")
        oss_list = []
        err_reason = "not_supported"
    except yaml.YAMLError:
        if print_log:
            _logger.warning(f"Error to parse yaml - skip to parse yaml file: {yaml_file}")
        oss_list = []
        err_reason = "yaml_error"
    return oss_list, set(license_list), err_reason


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
    elif key == 'yocto_package':
        oss.yocto_package = value
    elif key == 'yocto_recipe':
        oss.yocto_recipe = value
    else:
        if yaml_file != "":
            _logger.debug(f"file:{yaml_file} - key:{key} cannot be parsed")
