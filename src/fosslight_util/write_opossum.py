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
from typing import Dict, Optional

import fosslight_util.constant as constant
from fosslight_util.write_excel import remove_empty_sheet

FL_SOURCE = 'FL_Source'
FL_DEPENDENCY = 'FL_Dependency'
FL_BINARY = 'FL_Binary'
_supported_sheet_name = ['SRC_' + FL_SOURCE, 'SRC_' + FL_DEPENDENCY, 'BIN_' + FL_BINARY]

PACKAE = {
    'requirements.txt': 'pypi',
    'package.json': 'npm',
    'pom.xml': 'maven',
    'build.gradle': 'gradle',
    'pubspec.yaml': 'pub',
    'Podfile.lock': 'cocoapods',
    'Package.resolved': 'swift',
    'Cartfile.resolved': 'carthage'
}

_attributionConfidence = 80
logger = logging.getLogger(constant.LOGGER_NAME)


class AttributionItem():
    def __init__(self,
                 source_name: str,
                 licenseName: str,
                 exclude: bool,
                 copyright: Optional[str] = None,
                 packageName: Optional[str] = None,
                 packageVersion: Optional[str] = None,
                 url: Optional[str] = None,
                 packageType: Optional[str] = None):
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
    def __init__(self,
                 source_name: str,
                 licenseName: str,
                 exclude: bool,
                 copyright: Optional[str] = None,
                 packageName: Optional[str] = None,
                 packageVersion: Optional[str] = None,
                 url: Optional[str] = None,
                 packageType: Optional[str] = None):
        super().__init__(source_name, licenseName, exclude, copyright=copyright,
                         packageName=packageName, packageVersion=packageVersion, url=url, packageType=packageType)

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
        elif self.source_name == FL_BINARY:
            dict[copyright] = self.copyright
            dict[packageName] = self.packageName
            dict[packageVersion] = self.packageVersion
            dict[url] = self.url
        elif self.source_name == FL_DEPENDENCY:
            dict[copyright] = self.copyright
            dict[packageName] = self.packageName
            dict[packageVersion] = self.packageVersion
            dict[url] = self.url
            dict[packageType] = self.packageType

        return {key: value for key, value in dict.items() if value is not None}


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
    frequentLicensesFile = os.path.join("resources", "frequentLicenselist.json")
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


def write_opossum(filename, sheet_list):
    success = True
    error_msg = ''
    dict = {}
    _metadata_key = 'metadata'
    _resources_key = 'resources'
    _externalAttributions_key = 'externalAttributions'
    _resourcesToAttributions_key = 'resourcesToAttributions'
    _filesWithChildren_key = 'filesWithChildren'
    _attributionBreakpoints_key = 'attributionBreakpoints'

    is_not_null, sheet_list = remove_empty_sheet(sheet_list)

    if is_not_null:
        output_dir = os.path.dirname(filename)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        success, dict[_metadata_key] = make_metadata()
        resources = {}
        fc_list = []
        dict[_resources_key] = {}
        dict[_externalAttributions_key] = {}
        dict[_resourcesToAttributions_key] = {}
        filesWithChildren_list = []
        attributionBreakpoints_list = []
        try:
            for sheet_name, sheet_contents in sheet_list.items():
                if sheet_name in _supported_sheet_name:
                    scanner = '_'.join(sheet_name.split('_')[1:])
                else:
                    logger.warning("Not supported scanner(sheet_name):" + sheet_name)
                    continue

                ret_resources_attribution = make_resources_and_attributions(sheet_contents, scanner, resources, fc_list)
                success, rsc, ea, ra, fl, ab = ret_resources_attribution
                if success:
                    dict[_resources_key].update(rsc)
                    dict[_externalAttributions_key].update(ea)
                    dict[_resourcesToAttributions_key].update(ra)
                    filesWithChildren_list.extend(fl)
                    attributionBreakpoints_list.extend(ab)

            if success:
                dict[_filesWithChildren_key] = filesWithChildren_list
                dict[_attributionBreakpoints_key] = attributionBreakpoints_list
                frequentLicenses, success, error_msg = make_frequentlicenses()
                dict.update(frequentLicenses)

                opossum_json = json.dumps(dict)
                with open(filename, 'w+') as json_f:
                    json_f.write(opossum_json)
        except Exception as e:
            error_msg = 'Failed to write opossum json' + str(e)
            logger.error(traceback.format_exc())
    else:
        success = False
        error_msg = 'No item to write in output file.'

    return success, error_msg


def make_resources(path, resources):
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
        logger.error("Failed to make resources: " + str(e) + traceback.format_exc())

    return resources


def make_resources_and_attributions(sheet_items, scanner, resources, fc_list):
    success = True
    resourcesToAttributions = {}
    externalAttributions: Dict[str, Attribution] = {}
    externalAttribution_list = []
    ab_list = []

    try:
        for items in sheet_items:
            path, oss_name, oss_version, license, url, homepage, copyright, exclude, comment = items

            if scanner == FL_SOURCE:
                if (os.path.join(os.sep, path) + os.sep) not in fc_list:
                    resources = make_resources(path, resources)
                attribution = Attribution(scanner, license, exclude, copyright)
            elif scanner == FL_BINARY:
                resources = make_resources(path, resources)
                attribution = Attribution(scanner, license, exclude, copyright, oss_name, oss_version, url)
            elif scanner == FL_DEPENDENCY:
                packageType = PACKAE[path]
                if (os.path.join(os.sep, path) + os.sep) not in fc_list:
                    fc_list.append(os.path.join(os.sep, path) + os.sep)
                    ab_list.append(os.path.join(os.sep, path, packageType) + os.sep)
                    if path in resources.keys():
                        del resources[path]
                path = os.path.join(path, packageType, oss_name)
                resources = make_resources(path, resources)
                attribution = Attribution(scanner, license, exclude,
                                          copyright, oss_name, oss_version, url, packageType)
            else:
                logger.error("Not supported scanner:" + scanner)
                break

            find_same_attribution = False
            uuid = ''
            for externalAttribution in externalAttributions.values():
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
                externalAttributions[str(ext.uuid)] = ext
    except Exception as e:
        logger.error("Failed to make_resources_and_attributions: " + str(e))
        logger.error(traceback.format_exc())
        success = False

    externalAttributionsConverted = {
        uuid: ext.get_externalAttribution_dict() for uuid, ext in externalAttributions.items()
    }

    return success, resources, externalAttributionsConverted, resourcesToAttributions, fc_list, ab_list
