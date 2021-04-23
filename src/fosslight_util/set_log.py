#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from pathlib import Path


def init_log(log_file, create_file=True):

    logger = logging.getLogger('fosslight')
    if not logger.hasHandlers():
        log_level = logging.WARNING
        formatter = logging.Formatter('%(message)s')

        log_dir = os.path.dirname(log_file)
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        if create_file:
            file_hanlder = logging.FileHandler(log_file)
            file_hanlder.setLevel(log_level)
            file_hanlder.setFormatter(formatter)
            file_hanlder.propagate = False
            logger.addHandler(file_hanlder)

        console = logging.StreamHandler()
        console.setLevel(log_level)
        console.setFormatter(formatter)
        console.propagate = False
        logger.addHandler(console)

        logger.propagate = False

    return logger
