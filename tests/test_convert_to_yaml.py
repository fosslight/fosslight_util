#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
from fosslight_util.set_log import init_log
from fosslight_util.convert_excel_to_yaml import convert_excel_to_yaml


def main():
    output_dir = "test_result/convert"
    logger, _result_log = init_log(os.path.join(output_dir, "convert_result.txt"))
    logger.warning("TESTING - converting excel to yaml")
    output_yaml = os.path.join(os.path.abspath(output_dir), "fosslight-sbom-info")
    logger.warning(f"output_yaml - {output_yaml}")
    convert_excel_to_yaml("tests/FOSSLight-Report_sample.xlsx", output_yaml)


if __name__ == '__main__':
    main()
