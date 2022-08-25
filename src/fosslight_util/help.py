#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import sys
import pkg_resources

_HELP_MESSAGE_COMMON = """
     ____      _____      ____       ____       __                         __         __      
    /\  _`\   /\  __`\   /\  _`\    /\  _`\    /\ \        __             /\ \       /\ \__   
    \ \ \L\_\ \ \ \/\ \  \ \,\L\_\  \ \,\L\_\  \ \ \      /\_\       __   \ \ \___   \ \ ,_\  
     \ \  _\/  \ \ \ \ \  \/_\__ \   \/_\__ \   \ \ \  __ \/\ \    /'_ `\  \ \  _ `\  \ \ \/  
      \ \ \/    \ \ \_\ \   /\ \L\ \   /\ \L\ \  \ \ \L\ \ \ \ \  /\ \L\ \  \ \ \ \ \  \ \ \_ 
       \ \_\     \ \_____\  \ `\____\  \ `\____\  \ \____/  \ \_\ \ \____ \  \ \_\ \_\  \ \__\ 
        \/_/      \/_____/   \/_____/   \/_____/   \/___/    \/_/  \/___L\ \  \/_/\/_/   \/__/
                                                                     /\____/                     
                                                                     \_/__/                      
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
