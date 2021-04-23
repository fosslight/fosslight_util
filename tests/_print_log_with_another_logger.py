#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging


def print_log_another_logger():
    logger = logging.getLogger('ANOTHER_LOGGER_TEST')

    log_level = logging.WARNING
    formatter = logging.Formatter('%(message)s')

    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(formatter)
    console.propagate = False
    logger.addHandler(console)

    logger.warning("Print log by using anther logger")
