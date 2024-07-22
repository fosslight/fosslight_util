#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from fosslight_util.help import print_package_version


class CoverItem:
    tool_name_key = "Tool information"
    start_time_key = "Start time"
    python_ver_key = "Python version"
    analyzed_path_key = "Analyzed path"
    excluded_path_key = "Excluded path"
    comment_key = "Comment"

    PKG_NAMES = [
        "fosslight_scanner",
        "fosslight_source",
        "fosslight_dependency",
        "fosslight_binary"
    ]

    def __init__(self, tool_name="", start_time="", input_path="", comment="", exclude_path=[], simple_mode=True):
        if simple_mode:
            self.tool_name = f'{tool_name} v{print_package_version(tool_name, "", False)}'
        else:
            first_pkg = f'{self.PKG_NAMES[0]} v{print_package_version(self.PKG_NAMES[0], "", False)}'
            remaining_pkgs = ", ".join([
                f'{pkg_name} v{print_package_version(pkg_name, "", False)}'
                for pkg_name in self.PKG_NAMES[1:]
            ])
            self.tool_name = f'{first_pkg} ({remaining_pkgs})'

        if start_time:
            date, time = start_time.split('_')
            self.start_time = f'{date}, {time[0:2]}:{time[2:4]}'
        else:
            self.start_time = ""
        self.input_path = os.path.abspath(input_path)
        self.exclude_path = ", ".join(exclude_path)
        self.comment = comment

        self.python_version = f'{sys.version_info.major}.{sys.version_info.minor}'

    def __del__(self):
        pass

    def get_print_json(self):
        json_item = {}
        json_item[self.tool_name_key] = self.tool_name
        json_item[self.start_time_key] = self.start_time
        json_item[self.python_ver_key] = self.python_version
        json_item[self.analyzed_path_key] = self.input_path
        json_item[self.excluded_path_key] = self.exclude_path
        json_item[self.comment_key] = self.comment

        return json_item
