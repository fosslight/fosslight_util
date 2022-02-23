#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.download import cli_download_and_extract


def main():
    cli_download_and_extract("https://github.com/LGE-OSS/example",
                             "test_result/download/example", "test_result/download_log/example")
    cli_download_and_extract("https://pypi.org/project/filelock/3.4.1",
                             "test_result/download/filelock", "test_result/download_log/filelock")


if __name__ == '__main__':
    main()
