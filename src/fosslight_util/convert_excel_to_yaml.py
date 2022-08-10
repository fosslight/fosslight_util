#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import sys
import logging
import yaml
import re
from fosslight_util.constant import LOGGER_NAME
from fosslight_util.write_yaml import create_yaml_with_ossitem
from fosslight_util.read_excel import read_oss_report

logger = logging.getLogger(LOGGER_NAME)


def find_report_file(path_to_find):
    file_to_find = ["FOSSLight-Report.xlsx", "OSS-Report.xlsx"]

    try:
        for file in file_to_find:
            file_with_path = os.path.join(path_to_find, file)
            if os.path.isfile(file_with_path):
                return file
        for root, dirs, files in os.walk(path_to_find):
            for file in files:
                file_name = file.lower()
                p = re.compile(r"[\s\S]*OSS[\s\S]*-Report[\s\S]*.xlsx", re.I)
                if p.search(file_name):
                    return os.path.join(root, file)
    except Exception as error:
        logger.debug("Find report:"+str(error))
    return ""


def convert_excel_to_yaml(oss_report_to_read, output_file, sheet_names=""):
    _file_extension = ".yaml"
    yaml_dict = {}

    if os.path.isfile(oss_report_to_read):
        try:
            items = read_oss_report(oss_report_to_read, sheet_names)
            for item in items:
                create_yaml_with_ossitem(item, yaml_dict)
            if yaml_dict:
                output_file = output_file if output_file.endswith(_file_extension) else output_file + _file_extension
                success = write_yaml_file(output_file, yaml_dict)
                if success:
                    logger.warning(f"Output: {output_file}")
                else:
                    logger.error(f"Can't write yaml file : {output_file}")
                    sys.exit(1)
        except Exception as error:
            logger.error(f"Convert yaml: {error}")
    else:
        logger.error(f"Can't find a file: {oss_report_to_read}")


def write_yaml_file(output_file, json_output):
    success = True
    error_msg = ""

    try:
        with open(output_file, 'w') as f:
            yaml.dump(json_output, f, sort_keys=False)
    except Exception as ex:
        error_msg = str(ex)
        success = False
    return success, error_msg
