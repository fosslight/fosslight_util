#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import List, Dict
from fosslight_util.constant import LOGGER_NAME
from fosslight_util.oss_item import FileItem

logger = logging.getLogger(LOGGER_NAME)
VERSION = 'version'
LICENSE = 'license'
NAME = 'name'


def compare_yaml(before_fileitems: List[FileItem], after_fileitems: List[FileItem]) -> Dict[str, List]:
    bf_raw = []
    af_raw = []
    for bf in before_fileitems:
        bf_raw.extend(bf.get_print_json())
    for af in after_fileitems:
        af_raw.extend(af.get_print_json())

    before_items = get_merged_item(bf_raw)
    after_items = get_merged_item(af_raw)

    new_before = []
    for bi in before_items:
        if bi in after_items:
            after_items.remove(bi)
        else:
            new_before.append(bi)

    ADD = "add"
    DELETE = "delete"
    CHANGE = "change"
    PREV = "prev"
    NOW = "now"

    comp_out = {ADD: [], DELETE: [], CHANGE: []}

    b_name = set([bi[NAME] for bi in new_before])
    a_name = set([ai[NAME] for ai in after_items])

    removed_name = b_name - a_name
    changed_name = b_name - removed_name
    added_name = a_name - changed_name

    for bi in new_before:
        if bi[NAME] in removed_name:
            comp_out[DELETE].append(bi)
        elif bi[NAME] in changed_name:
            filtered = next(filter(lambda oss_dict: oss_dict[NAME] == bi[NAME], comp_out[CHANGE]), None)
            if filtered:
                bi.pop(NAME)
                filtered[PREV].append(bi)
            else:
                item_info = {NAME: bi[NAME], PREV: [], NOW: []}
                bi.pop(NAME)
                item_info[PREV].append(bi)
                comp_out[CHANGE].append(item_info)

    for ai in after_items:
        if ai[NAME] in added_name:
            comp_out[ADD].append(ai)
        elif ai[NAME] in changed_name:
            filtered = next(filter(lambda oss_dict: oss_dict[NAME] == ai[NAME], comp_out[CHANGE]), None)
            if filtered:
                ai.pop(NAME)
                filtered[NOW].append(ai)

    return comp_out


def get_merged_item(oss_items):
    item_list = []
    for oi in oss_items:
        if oi.get("exclude", None):
            continue
        oi_name = oi.get("name", '')
        oi_version = oi.get("version", '')
        oi_license = oi.get("license", '')
        if not (oi_name and oi_version and oi_license):
            continue
        item_info = {NAME: oi_name, VERSION: oi_version, LICENSE: oi_license}

        filtered = next(filter(lambda oss_dict: oss_dict[NAME] == oi_name and oss_dict[VERSION] == oi_version, item_list), None)
        if filtered:
            filtered[LICENSE].extend(oi_license)
            filtered[LICENSE] = list(set(filtered[LICENSE]))
        else:
            item_list.append(item_info)

    return item_list
