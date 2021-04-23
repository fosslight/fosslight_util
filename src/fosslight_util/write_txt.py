#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
from pathlib import Path


def write_txt_file(file_to_create, str_to_write):
    success = True
    error_msg = ""
    try:
        dir_to_create = os.path.dirname(file_to_create)
        Path(dir_to_create).mkdir(parents=True, exist_ok=True)
        f = open(file_to_create, 'w')
        f.write(str_to_write)
        f.close()
    except Exception as ex:
        error_msg = str(ex)
        success = False
    return success, error_msg
