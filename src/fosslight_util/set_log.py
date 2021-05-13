#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from pathlib import Path
import pkg_resources
import sys
import platform
from . import constant as constant


def init_log(log_file, create_file=True, stream_log_level=logging.WARN, file_log_level=logging.INFO):

    logger = logging.getLogger(constant.LOGGER_NAME)
    
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        log_dir = os.path.dirname(log_file)
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        if create_file:

            file_handlder = logging.FileHandler(log_file)
            file_handlder.setLevel(file_log_level)
            file_formatter = logging.Formatter('[%(levelname)7s] %(message)s')
            file_handlder.setFormatter(file_formatter)
            file_handlder.propagate = False
            logger.addHandler(file_handlder)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(stream_log_level)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        console_handler.propagate = False
        logger.addHandler(console_handler)

        logger.propagate = False

    return logger


def init_log_item(main_package_name="", path_to_analyze= ""):

    _PYTHON_VERSION = sys.version_info[0]
    _result_log = {
        "Tool Info": main_package_name,
        "Python version": _PYTHON_VERSION,
        "OS": platform.system()+" "+platform.release(),
    }
    if main_package_name != "":
        pkg_version = pkg_resources.get_distribution(main_package_name).version
        _result_log["Tool Info"] = main_package_name +" v."+pkg_version
    if path_to_analyze != "":
       _result_log["Path to analyze"] = path_to_analyze

    return _result_log
