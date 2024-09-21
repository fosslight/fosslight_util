#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import json
from fosslight_util.compare_yaml import compare_yaml


def main():
    cur = os.getcwd() + '/tests'
    result = compare_yaml(os.path.join(cur, 'before.yaml'), os.path.join(cur, 'after.yaml'))
    print(json.dumps(result, indent=4, sort_keys=True))


if __name__ == '__main__':
    main()
