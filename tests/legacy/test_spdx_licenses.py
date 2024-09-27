#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.set_log import init_log
from fosslight_util.spdx_licenses import get_spdx_licenses_json


def main():
    logger, _result_log = init_log("test_result/spdx_licenses/log_spdx_licenses.txt")
    logger.warning("TESTING - Get spdx licenses")

    success, error_msg, licenses = get_spdx_licenses_json()
    logger.warning("Result:" + str(success) + ", error_msg:" + error_msg)


if __name__ == '__main__':
    main()
