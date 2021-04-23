#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

from fosslight_util.set_log import init_log

logger = ""


def print_log():
    global logger

    logger = init_log("test_result/log_file2.txt")
    logger.warning("TESTING LOG - from 2nd Module")

    print_log_in_function()


def print_log_in_function():
    logger.warning("TESTING LOG - from function in 2nd Module")
