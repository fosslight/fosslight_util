#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import yaml
from fosslight_util.set_log import init_log, init_log_item
from _print_log import print_log
from _print_log_with_another_logger import print_log_another_logger
import logging


def main():
    logger = init_log("test_result/log_file1.txt", True, logging.WARNING)
    logger.debug('Error! This message is a level that should not be displayed on the console.')
    logger.info('Error! This message is a level that should not be displayed on the console.')
    logger.warning('This message is a level that should be displayed on the console.')
    
    result_log = init_log_item("fosslight_util")
    _str_final_result_log = yaml.safe_dump(result_log, allow_unicode=True)
    logger.warning(_str_final_result_log)

    print_log()
    print_log_another_logger()


if __name__ == '__main__':
    main()
