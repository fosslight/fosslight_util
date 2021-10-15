#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
import traceback
import fosslight_util.constant as constant
from fosslight_util.write_excel import remove_empty_sheet

FL_SOURCE = 'FL-Source'
FL_DEPENDENCY = 'FL-Dependency'
_attributionConfidence = 80
logger = logging.getLogger(constant.LOGGER_NAME)


class AttributionItem():
    def __init__(self, source_name, licenseName, exclude,
                 copyright='', packageType='', packageName='', packageVersion='', url=''):
        self.attributionConfidence = _attributionConfidence
        self.documentConfidence = _attributionConfidence
        if exclude:
            self.excludeFromNotice = True
        else:
            self.excludeFromNotice = False

        self.source_name = source_name
        if source_name == FL_DEPENDENCY:
            self.preSelected = True
        else:
            self.preSelected = False

        self.licenseName = licenseName
        self.copyright = copyright
        self.packageType = packageType
        self.packageName = packageName
        self.packageVersion = packageVersion
        self.url = url


class Attribution(AttributionItem):
    def __init__(self, source_name, licenseName, exclude,
                 copyright='', packageType='', packageName='', packageVersion='', url=''):
        super().__init__(source_name, licenseName, exclude, copyright=copyright,
                         packageType=packageType, packageName=packageName, packageVersion=packageVersion, url=url)

        self.uuid = uuid.uuid4()

    def __eq__(self, other):
        if not isinstance(other, Attribution):
            return NotImplemented

        return self.source_name == other.source_name and self.licenseName == other.licenseName and \
            self.copyright == other.copyright and self.packageType == other.packageType and \
            self.packageName == other.packageName and self.packageVersion == other.packageVersion and \
            self.url == other.url

    def get_externalAttribution_dict(self):
        dict = {}
        attributionConfidence = 'attributionConfidence'
        copyright = 'copyright'
        excludeFromNotice = 'excludeFromNotice'
        licenseName = 'licenseName'
        preSelected = 'preSelected'
        source = 'source'
        documentConfidence = 'documentConfidence'
        name = 'name'
        packageName = 'packageName'
        packageType = 'packageType'
        packageVersion = 'packageVersion'
        url = 'url'

        dict[attributionConfidence] = self.attributionConfidence

        dict[source] = {}
        dict[source][documentConfidence] = self.documentConfidence
        dict[source][name] = self.source_name

        dict[excludeFromNotice] = self.excludeFromNotice
        dict[licenseName] = self.licenseName
        dict[preSelected] = self.preSelected

        if self.source_name == FL_SOURCE:
            dict[copyright] = self.copyright
        elif self.source_name == FL_DEPENDENCY:
            dict[packageName] = self.packageName
            dict[packageType] = self.packageType
            dict[packageVersion] = self.packageVersion
            dict[url] = self.url

        return dict


def make_metadata():
    success = True
    metadata = {}
    _projectId = 'projectId'
    _fileCreationDate = 'fileCreationDate'

    _start_time = datetime.now().strftime('%Y-%m-%dT%H%M%S')

    metadata[_projectId] = str(0)
    metadata[_fileCreationDate] = _start_time

    return success, metadata


def make_frequentlicenses():
    success = True
    error_msg = ''
    frequentLicenses = {}
    frequentLicensesFile = "frequentLicenselist.json"
    try:
        base_dir = sys._MEIPASS
    except Exception:
        base_dir = os.path.dirname(__file__)
    file_withpath = os.path.join(base_dir, frequentLicensesFile)

    try:
        with open(file_withpath, 'r', encoding='utf8') as f:
            frequentLicenses = json.load(f)
    except Exception as e:
        success = False
        error_msg = 'Failed to open and parse ' + str(file_withpath)
        logger.error(error_msg + ": " + str(e))
        logger.error(traceback.format_exc())

    return frequentLicenses, success, error_msg


def write_opossum(filename, sheet_list, scanner):
    success = True
    error_msg = ''
    dict = {}
    _src_sheetname = 'SRC'
    _metadata_key = 'metadata'
    _resources_key = 'resources'
    _externalAttributions_key = 'externalAttributions'
    _resourcesToAttributions_key = 'resourcesToAttributions'

    is_not_null, sheet_list = remove_empty_sheet(sheet_list)

    if is_not_null:
        output_dir = os.path.dirname(filename)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        success, dict[_metadata_key] = make_metadata()
        if success:
            ret_resources_attribution = make_resources_and_attributions(sheet_list[_src_sheetname], scanner)
            success, resources, externalAttributions, resourcesToAttributions = ret_resources_attribution

        if success:
            dict[_resources_key] = resources
            dict[_externalAttributions_key] = externalAttributions
            dict[_resourcesToAttributions_key] = resourcesToAttributions

            frequentLicenses, success, error_msg = make_frequentlicenses()
            if success:
                dict.update(frequentLicenses)

                opossum_json = json.dumps(dict)

                with open(filename, 'w+') as json_f:
                    json_f.write(opossum_json)

        else:
            success = False
            error_msg = 'Failed to write opossum json'
    else:
        success = False
        error_msg = 'No item to write in output file.'

    return success, error_msg


def make_resources(path, resources):
    succuess = True

    files = os.path.basename(path)
    dirs = os.path.dirname(path).split(os.sep)

    try:
        if not dirs[0]:
            resources[files] = 1
        else:
            tmp = resources
            for dir in dirs:
                tmp = tmp.setdefault(dir, {})
                if dir == dirs[-1]:
                    tmp[files] = 1
    except Exception as e:
        logger.error("Failed to make resources: " + str(e))
        succuess = False

    return succuess, resources


def make_resources_and_attributions(sheet_items, scanner):
    success = True
    resources = {}
    resourcesToAttributions = {}
    externalAttributions = {}
    externalAttribution_list = []

    try:
        for items in sheet_items:
            path, oss_name, oss_version, license, url, homepage, copyright, exclude, comment = items

            if scanner == FL_SOURCE:
                success, resources = make_resources(path, resources)
                attribution = Attribution(scanner, license, exclude, copyright)
            elif scanner == FL_DEPENDENCY:
                # todo : make filesWithChildren, attributionBreakpoints (optional field)
                attribution = Attribution(scanner, license, exclude,
                                          copyright, packageType='', packageName='', packageVersion='', url='')
                pass

            find_same_attribution = False
            uuid = ''
            for externalAttribution in externalAttributions:
                if attribution == externalAttribution:
                    find_same_attribution = True
                    uuid = externalAttribution.uuid
                    del attribution
                    break

            if not find_same_attribution:
                externalAttribution_list.append(attribution)
                uuid = attribution.uuid

            uuid_list = []
            uuid_list.append(str(uuid))
            resourcesToAttributions[os.path.join(os.sep, path)] = uuid_list

            for ext in externalAttribution_list:
                dict = ext.get_externalAttribution_dict()
                externalAttributions[str(ext.uuid)] = dict
    except Exception as e:
        logger.error("Failed to make_resources_and_attributions: " + str(e))
        logger.error(traceback.format_exc())
        success = False

    return success, resources, externalAttributions, resourcesToAttributions
