#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.download import cli_download_and_extract


def main():
    success, msg, _, _ = cli_download_and_extract("https://github.com/LGE-OSS/example",
                                                  "test_result/download/example",
                                                  "test_result/download_log/example")
    if not success:
        raise Exception(f"Download failed with git:{msg}")
    success, msg, _, _ = cli_download_and_extract("https://pypi.org/project/filelock/3.4.1",
                                                  "test_result/download/filelock",
                                                  "test_result/download_log/filelock")
    if not success:
        raise Exception(f"Download failed with wget:{msg}")


if __name__ == '__main__':
    main()
