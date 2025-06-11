#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import sys
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError  # Python <3.8

_HELP_MESSAGE_COMMON = """
         _______  _______  _______  _______  ___      ___           __
        |       ||       ||       ||       ||   |    |___|         |  |         _
        |    ___||   _   ||  _____||  _____||   |     ___          |  |____  __| |__
        |   |___ |  | |  || |_____ | |_____ |   |    |   | _______ |   _   ||__   __|
        |    ___||  |_|  ||_____  ||_____  ||   |___ |   ||   _   ||  | |  |   | |
        |   |    |       | _____| | _____| ||       ||   ||  |_|  ||  | |  |   | |__
        |___|    |_______||_______||_______||_______||___||____   ||__| |__|   |____|
                                                               |  |
                                                           ____|  |
                                                          |_______|
"""


_HELP_MESSAGE_DOWNLOAD = """
    FOSSLight Downloader is a tool to download the package via input URL

    Usage: fosslight_download [option1] <arg1> [options2] <arg2>
     ex) fosslight_download -s http://github.com/fosslight/fosslight -t output_dir -d log_dir

    Required:
        -s\t\t      URL of the package to be downloaded

    Optional:
        -h\t\t      Print help message
        -t\t\t      Output path name
        -d\t\t      Directory name to save the log file"""


class PrintHelpMsg():

    def __init__(self, value: str = ""):
        self.message_suffix = value

    def print_help_msg(self, exitopt: bool) -> None:
        print(_HELP_MESSAGE_COMMON)
        print(self.message_suffix)

        if exitopt:
            sys.exit()


def print_package_version(pkg_name: str, msg: str = "", exitopt: bool = True) -> str:
    if msg == "":
        msg = f"{pkg_name} Version:"
    try:
        cur_version = version(pkg_name)
    except PackageNotFoundError:
        cur_version = "unknown"

    if exitopt:
        print(f'{msg} {cur_version}')
        sys.exit(0)
    else:
        return cur_version


def print_help_msg_download(exitOpt=True):
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_DOWNLOAD)
    helpMsg.print_help_msg(exitOpt)
