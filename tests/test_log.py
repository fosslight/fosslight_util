#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

from fosslight_util.set_log import init_log
from _print_log import print_log
from _print_log_with_another_logger import print_log_another_logger

def main():
    logger = init_log("test_result/log_file1.txt")
    logger.warning("TESTING LOG - from 1st Module")
    
    print_log()
    print_log_another_logger()

if __name__ == '__main__':
    main()
