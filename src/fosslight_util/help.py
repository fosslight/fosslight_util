#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import sys
import pkg_resources

_HELP_MESSAGE_COMMON = """
         _______  _______  _______  _______  ___      ___   _______  __   __  _______
        |       ||       ||       ||       ||   |    |   | |       ||  | |  ||       |
        |    ___||   _   ||  _____||  _____||   |    |   | |    ___||  |_|  ||_     _|
        |   |___ |  | |  || |_____ | |_____ |   |    |   | |   | __ |       |  |   |
        |    ___||  |_|  ||_____  ||_____  ||   |___ |   | |   ||  ||   _   |  |   |
        |   |    |       | _____| | _____| ||       ||   | |   |_| ||  | |  |  |   |
        |___|    |_______||_______||_______||_______||___| |_______||__| |__|  |___|
        """


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
        msg = f"{pkg_name} Version :"
    cur_version = pkg_resources.get_distribution(pkg_name).version
    print(f'{msg} {cur_version}')

    if exitopt:
        sys.exit(0)
