#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from fosslight_util.constant import LOGGER_NAME
from fosslight_util.parsing_yaml import parsing_yml

logger = logging.getLogger(LOGGER_NAME)
_version = 'version'
_license = 'license'
_name = 'name'


def compare_yaml(before_file, after_file):
    before_oss_items, _ = parsing_yml(os.path.basename(before_file), os.path.dirname(before_file))
    after_oss_items, _ = parsing_yml(os.path.basename(after_file), os.path.dirname(after_file))

    before_items = get_merged_item(before_oss_items)
    after_items = get_merged_item(after_oss_items)

    new_before = []
    for bi in before_items:
        if bi in after_items:
            after_items.remove(bi)
        else:
            new_before.append(bi)

    _add = "add"
    _delete = "delete"
    _change = "change"
    _prev = "prev"
    _now = "now"

    comp_out = {_add: [], _delete: [], _change: []}

    b_name = list(set([bi[_name] for bi in new_before]))
    a_name = list(set([ai[_name] for ai in after_items]))

    removed_name = [bn for bn in b_name if bn not in a_name]
    changed_name = list(set(b_name) ^ set(removed_name))
    added_name = list(set(a_name) ^ set(changed_name))

    for bi in new_before:
        if bi[_name] in removed_name:
            comp_out[_delete].append(bi)
        elif bi[_name] in changed_name:
            name_find = False
            for ci in comp_out[_change]:
                if ci[_name] == bi[_name]:
                    bi.pop(_name)
                    ci[_prev].append(bi)
                    name_find = True
                    break
            if not name_find:
                item_info = {_name: bi[_name], _prev: [], _now: []}
                bi.pop(_name)
                item_info[_prev].append(bi)
                comp_out[_change].append(item_info)

    for ai in after_items:
        if ai[_name] in added_name:
            comp_out[_add].append(ai)
        elif ai[_name] in changed_name:
            for ci in comp_out[_change]:
                if ci[_name] == ai[_name]:
                    ai.pop(_name)
                    ci[_now].append(ai)
                    break

    return comp_out


def get_merged_item(oss_items):
    item_list = []
    for oi in oss_items:
        item_info = {_name: oi.name, _version: oi.version, _license: oi.license}

        version_find = False
        for ii in item_list:
            if oi.name == ii[_name] and oi.version == ii[_version]:
                ii[_license].extend(oi.license)
                ii[_license] = list(set(ii[_license]))
                version_find = True
                break
        if not version_find:
            item_list.append(item_info)

    return item_list
