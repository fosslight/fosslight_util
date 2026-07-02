#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import re
import sys
import yaml
from datetime import datetime
from fosslight_util.help import print_package_version


def _format_display_time(value):
    return datetime.strptime(value, '%Y%m%d_%H%M%S').strftime('%Y%m%d_%H:%M:%S')


def _format_duration_compact(total_seconds):
    hours, remaining_seconds = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remaining_seconds, 60)

    duration_items = []
    if hours > 0:
        duration_items.append(f'{hours}h')
    if minutes > 0:
        duration_items.append(f'{minutes}m')
    duration_items.append(f'{seconds}s')
    return f'({" ".join(duration_items)})'


def format_running_time(start_time, finish_time):
    start_datetime = datetime.strptime(start_time, '%Y%m%d_%H%M%S')
    finish_datetime = datetime.strptime(finish_time, '%Y%m%d_%H%M%S')
    total_seconds = int((finish_datetime - start_datetime).total_seconds())

    start_display = start_datetime.strftime('%Y%m%d_%H:%M:%S')
    finish_display = finish_datetime.strftime('%Y%m%d_%H:%M:%S')
    duration = _format_duration_compact(total_seconds)

    return f'{start_display} ~ {finish_display} {duration}'


def dump_result_log(result_log):
    log_text = yaml.safe_dump(result_log, allow_unicode=True, sort_keys=True)
    log_text = re.sub(r"Running time: ['\"](.+?)['\"]\n", r"Running time: \1\n", log_text)
    return log_text.strip()


class CoverItem:
    tool_name_key = "Tool information"
    start_time_key = "Running time"
    python_ver_key = "Python version"
    analyzed_path_key = "Analyzed path"
    excluded_path_key = "Excluded path"
    comment_key = "Comment"

    PKG_NAMES = [
        "fosslight_scanner",
        "fosslight_dependency",
        "fosslight_source",
        "fosslight_binary"
    ]

    def __init__(self, tool_name="", start_time="", input_path="", comment="", exclude_path=[], simple_mode=True,
                 finish_time=""):
        if simple_mode:
            self.tool_name = f'{tool_name} v{print_package_version(tool_name, "", False)}'
        else:
            first_pkg = f'{self.PKG_NAMES[0]} v{print_package_version(self.PKG_NAMES[0], "", False)}'
            remaining_pkgs = ", ".join([
                f'{pkg_name} v{print_package_version(pkg_name, "", False)}'
                for pkg_name in self.PKG_NAMES[1:]
            ])
            self.tool_name = f'{first_pkg} ({remaining_pkgs})'

        self.start_time = start_time
        self.finish_time = finish_time
        self.running_time = self._format_running_time()
        self.input_path = os.path.abspath(input_path)
        self.exclude_path = ", ".join(exclude_path)
        self.comment = comment

        self.python_version = f'{sys.version_info.major}.{sys.version_info.minor}'

    def __del__(self):
        pass

    def get_sort_order(self):
        for idx, pkg_name in enumerate(self.PKG_NAMES[1:], start=0):
            if pkg_name in self.tool_name:
                return idx
        return 999

    def __lt__(self, other):
        return self.get_sort_order() < other.get_sort_order()

    def set_finish_time(self, finish_time):
        self.finish_time = finish_time
        self.running_time = self._format_running_time()

    def _format_running_time(self):
        if not self.start_time:
            return ""

        if not self.finish_time:
            return _format_display_time(self.start_time)

        return format_running_time(self.start_time, self.finish_time)

    def create_merged_comment(self, cover_items):
        if not cover_items:
            return ""
        sorted_items = sorted(cover_items)
        comments = []
        for ci in sorted_items:
            comments.append(f'[{ci.tool_name}] {ci.comment}')
        return '\n'.join(comments)

    def get_print_json(self):
        json_item = {}
        json_item[self.tool_name_key] = self.tool_name
        json_item[self.start_time_key] = self.running_time
        json_item[self.python_ver_key] = self.python_version
        json_item[self.analyzed_path_key] = self.input_path
        json_item[self.excluded_path_key] = self.exclude_path
        json_item[self.comment_key] = self.comment

        return json_item
