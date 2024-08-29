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
from fosslight_util.constant import LOGGER_NAME, FOSSLIGHT_BINARY, FOSSLIGHT_DEPENDENCY, FOSSLIGHT_SOURCE
from typing import Dict, Optional, Tuple


PACKAGE = {
    'requirements.txt': 'pypi',
    'setup.py': 'pypi',
    'package.json': 'npm',
    'pom.xml': 'maven',
    'build.gradle': 'gradle',
    'pubspec.yaml': 'pub',
    'Podfile.lock': 'cocoapods',
    'Package.resolved': 'swift',
    'Cartfile.resolved': 'carthage',
    'go.mod': 'Go'
}

_attributionConfidence = 80
logger = logging.getLogger(LOGGER_NAME)


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
        if source_name == FOSSLIGHT_DEPENDENCY:
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

        if self.source_name == FOSSLIGHT_SOURCE or FOSSLIGHT_BINARY:
            dict[copyright] = self.copyright
            dict[packageName] = self.packageName
            dict[packageVersion] = self.packageVersion
            dict[url] = self.url
        elif self.source_name == FOSSLIGHT_DEPENDENCY:
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
        base_dir = os.path.join(sys._MEIPASS, vars(sys.modules[__name__])['__package__'])
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


def write_opossum(filename: str, scan_item) -> Tuple[bool, str]:
    success = True
    error_msg = ''
    dict = {}
    _metadata_key = 'metadata'
    _resources_key = 'resources'
    _externalAttributions_key = 'externalAttributions'
    _resourcesToAttributions_key = 'resourcesToAttributions'
    _filesWithChildren_key = 'filesWithChildren'
    _attributionBreakpoints_key = 'attributionBreakpoints'

    if scan_item:
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
            for scanner_name, _ in scan_item.file_items.items():
                sheet_contents = scan_item.get_print_array(scanner_name)
                ret_resources_attribution = make_resources_and_attributions(sheet_contents, scanner_name, resources, fc_list)
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
            items = items[0:9]
            path, oss_name, oss_version, license, url, homepage, copyright, exclude, comment = items

            if scanner == FOSSLIGHT_SOURCE:
                if (os.path.join(os.sep, path) + os.sep) not in fc_list:
                    resources = make_resources(path, resources)
                attribution = Attribution(scanner, license, exclude, copyright, oss_name, oss_version, url)
            elif scanner == FOSSLIGHT_BINARY:
                resources = make_resources(path, resources)
                attribution = Attribution(scanner, license, exclude, copyright, oss_name, oss_version, url)
            elif scanner == FOSSLIGHT_DEPENDENCY:
                try:
                    packageType = PACKAGE[path]
                except Exception:
                    packageType = ''
                    if path == '':
                        try_package_type = oss_name.split(':')[0]
                    else:
                        try_package_type = path.split(',')[0]
                    if try_package_type in PACKAGE.items():
                        packageType = try_package_type

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
            if os.path.join(os.sep, path) in resourcesToAttributions:
                resourcesToAttributions[os.path.join(os.sep, path)].extend(uuid_list)
            else:
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
