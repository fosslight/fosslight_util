#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from fosslight_util.help import print_package_version


class CoverItem:
    tool_name_key = "Tool name"
    tool_version_key = "Tool version"
    start_time_key = "Start time"
    python_ver_key = "Python version"
    analyzed_path_key = "Analyzed path"
    excluded_path_key = "Excluded path"
    comment_key = "Comment"

    def __init__(self, tool_name="", start_time="", input_path="", comment="", exclude_path=[]):
        self.tool_name = tool_name
        if start_time:
            date, time = start_time.split('_')
            self.start_time = f'{date}, {time[0:2]}:{time[2:4]}'
        else:
            self.start_time = ""
        self.input_path = os.path.abspath(input_path)
        self.exclude_path = ", ".join(exclude_path)
        self.comment = comment

        self.tool_version = print_package_version(self.tool_name, "", False)
        self.python_version = f'{sys.version_info.major}.{sys.version_info.minor}'

    def __del__(self):
        pass

    def get_print_json(self):
        json_item = {}
        json_item[self.tool_name_key] = self.tool_name
        json_item[self.tool_version_key] = self.tool_version
        json_item[self.start_time_key] = self.start_time
        json_item[self.python_ver_key] = self.python_version
        json_item[self.analyzed_path_key] = self.input_path
        json_item[self.excluded_path_key] = self.exclude_path
        json_item[self.comment_key] = self.comment

        return json_item
