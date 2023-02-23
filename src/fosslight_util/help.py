#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import sys
import pkg_resources

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
    message_suffix = ""

    def __init__(self, value):
        self.message_suffix = value

    def print_help_msg(self, exitopt):
        print(_HELP_MESSAGE_COMMON)
        print(self.message_suffix)

        if exitopt:
            sys.exit()


def print_package_version(pkg_name, msg="", exitopt=True):
    if msg == "":
        msg = f"{pkg_name} Version:"
    cur_version = pkg_resources.get_distribution(pkg_name).version
    print(f'{msg} {cur_version}')

    if exitopt:
        sys.exit(0)


def print_help_msg_download(exitOpt=True):
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_DOWNLOAD)
    helpMsg.print_help_msg(exitOpt)
