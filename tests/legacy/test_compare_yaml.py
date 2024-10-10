#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import json
from fosslight_util.compare_yaml import compare_yaml
from fosslight_util.parsing_yaml import parsing_yml


def main():
    cur = os.getcwd()
    resources = os.path.join(cur, 'resources')
    before_fileitems, _, _ = parsing_yml(os.path.join(resources, 'before.yaml'), resources)
    after_fileitems, _, _ = parsing_yml(os.path.join(resources, 'after.yaml'), resources)
    result = compare_yaml(before_fileitems, after_fileitems)
    print(json.dumps(result, indent=4, sort_keys=True))


if __name__ == '__main__':
    main()
