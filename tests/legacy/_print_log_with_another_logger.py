#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import fosslight_util.constant as constant


def print_log_another_logger():
    logger = logging.getLogger(constant.LOGGER_NAME)

    logger.warning("Print log by using anther logger")
