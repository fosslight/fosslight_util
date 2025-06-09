#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from pathlib import Path
import sys
import platform
from . import constant as constant
from lastversion import lastversion
import coloredlogs
from typing import Tuple
from logging import Logger

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError  # Python <3.8


def init_check_latest_version(pkg_version="", main_package_name=""):

    logger = logging.getLogger(constant.LOGGER_NAME)

    try:
        has_update = lastversion.has_update(repo=main_package_name, at='pip', current_version=pkg_version)
        if has_update:
            logger.info('### Version Info ###')
            logger.warning(f"Newer version is available : v{has_update}")
            logger.warning("You can update it with command ('"
                           f"pip install {main_package_name} --upgrade --force-reinstall')")
    except TypeError:
        logger.warning('Cannot check the lastest version on PIP')
        logger.warning('You could use already installed version\n')
    except Exception as error:
        logger.debug('Cannot check the latest version:' + str(error))


def get_os_version():

    logger = logging.getLogger(constant.LOGGER_NAME)

    os_version = platform.system() + " " + platform.release()
    if os_version == "Windows 10":
        try:
            windows_build = sys.getwindowsversion().build
            if windows_build >= 22000:
                os_version = "Windows 11"
        except Exception as error:
            logger.debug(str(error))
    return os_version


class CustomAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra):
        super(CustomAdapter, self).__init__(logger, {})
        self.extra = extra

    def process(self, msg, kwargs):
        return '[%s] %s' % (self.extra, msg), kwargs


def init_log(log_file: str, create_file: bool = True, stream_log_level: int = logging.INFO, file_log_level: int = logging.DEBUG,
             main_package_name: str = "", path_to_analyze: str = "", path_to_exclude: list = []) -> Tuple[Logger, dict]:

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
    logger = CustomAdapter(logger, main_package_name.upper())

    _PYTHON_VERSION = sys.version_info[0]
    _result_log = {
        "Tool Info": main_package_name,
        "Python version": _PYTHON_VERSION,
        "OS": get_os_version(),
    }
    if main_package_name != "":
        pkg_info = main_package_name
        try:
            pkg_version = version(main_package_name)
            init_check_latest_version(pkg_version, main_package_name)
            pkg_info = main_package_name + " v" + pkg_version
        except PackageNotFoundError:
            logger.debug('Cannot check the version: Package not found')
        except Exception as error:
            logger.debug('Cannot check the version:' + str(error))
        _result_log["Tool Info"] = pkg_info
    if path_to_analyze != "":
        _result_log["Path to analyze"] = path_to_analyze
    if path_to_exclude != []:
        _result_log["Path to exclude"] = ", ".join(path_to_exclude)

    return logger, _result_log
