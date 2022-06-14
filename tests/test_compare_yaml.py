#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
from fosslight_util.compare_yaml import compare_yaml


def main():
    cur = os.getcwd()
    print(compare_yaml(os.path.join(cur, 'before.yaml'), os.path.join(cur, 'after.yaml')))


if __name__ == '__main__':
    main()
