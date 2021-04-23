#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
from fosslight_util.set_log import init_log
from fosslight_util.write_txt import write_txt_file


def main():
    output_dir = "test_result/txt"
    logger = init_log(os.path.join(output_dir, "log.txt"))
    logger.warning("TESTING - writing text file")
    success, error_msg = write_txt_file(
        os.path.join(output_dir, "test.txt"), "Testing - Writing text in a file.")
    logger.warning("Result:" + str(success) + ", error_msg:"+error_msg)


if __name__ == '__main__':
    main()
