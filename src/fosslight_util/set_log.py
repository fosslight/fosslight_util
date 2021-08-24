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
from lastversion import lastversion
import coloredlogs


def init_check_latest_version(pkg_version="", main_package_name=""):

    logger = logging.getLogger(constant.LOGGER_NAME)

    try:
        has_update = lastversion.has_update(repo=main_package_name, at='pip', current_version=pkg_version)
        if has_update:
            logger.info('### Version Info ###')
            logger.warning('Newer version is available : v{}'.format(str(has_update)))
            logger.warning('You can update it with command (\'pip install ' + main_package_name + ' --upgrade\')')
    except TypeError:
        logger.warning('Cannot check the lastest version on PIP')
        logger.warning('You could use already installed version\n')
    except Exception as error:
        logger.debug('Cannot check the latest version:' + str(error))


def init_log(log_file, create_file=True, stream_log_level=logging.INFO,
             file_log_level=logging.DEBUG, main_package_name="", path_to_analyze=""):

    logger = logging.getLogger(constant.LOGGER_NAME)

    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        log_dir = os.path.dirname(log_file)
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        coloredlogs.DEFAULT_LOG_FORMAT = '%(message)s'
        coloredlogs.DEFAULT_LOG_LEVEL = stream_log_level
        coloredlogs.install(logger=logger)

        if create_file:
            file_handlder = logging.FileHandler(log_file)
            file_handlder.setLevel(file_log_level)
            file_formatter = logging.Formatter('[%(levelname)7s] %(message)s')
            file_handlder.setFormatter(file_formatter)
            file_handlder.propagate = False
            logger.addHandler(file_handlder)

        logger.propagate = False

    _PYTHON_VERSION = sys.version_info[0]
    _result_log = {
        "Tool Info": main_package_name,
        "Python version": _PYTHON_VERSION,
        "OS": platform.system()+" "+platform.release(),
    }
    if main_package_name != "":
        pkg_info = main_package_name
        try:
            pkg_version = pkg_resources.get_distribution(main_package_name).version
            init_check_latest_version(pkg_version, main_package_name)
            pkg_info = main_package_name + " v" + pkg_version
        except Exception as error:
            logger.debug('Cannot check the version:' + str(error))
        _result_log["Tool Info"] = pkg_info
    if path_to_analyze != "":
        _result_log["Path to analyze"] = path_to_analyze

    return logger, _result_log
