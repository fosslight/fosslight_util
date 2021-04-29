#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import yaml
from fosslight_util.set_log import init_log
from fosslight_util.set_log import init_log_item
from _print_log import print_log
from _print_log_with_another_logger import print_log_another_logger

def main():
    logger = init_log("test_result/log_file1.txt")
    logger.warning("TESTING LOG - from 1st Module")
    
    result_log = init_log_item("fosslight_util")
    _str_final_result_log = yaml.safe_dump(result_log, allow_unicode=True)
    logger.warning(_str_final_result_log)

    print_log()
    print_log_another_logger()

if __name__ == '__main__':
    main()
