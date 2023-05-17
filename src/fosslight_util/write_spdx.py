#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import uuid
import logging
import re
from pathlib import Path
from spdx.creationinfo import Tool
from spdx.document import Document
from spdx.package import Package
from spdx.relationship import Relationship
from spdx.document import License
from spdx.utils import SPDXNone
from spdx.utils import NoAssert
from spdx.version import Version
from spdx.writers import json
from spdx.writers import yaml
from spdx.writers import xml
from spdx.writers import tagvalue
from fosslight_util.spdx_licenses import get_spdx_licenses_json, get_license_from_nick
import fosslight_util.constant as constant
import traceback

logger = logging.getLogger(constant.LOGGER_NAME)


def get_license_list_version():
    version = 'N/A'
    success, error_msg, licenses = get_spdx_licenses_json()
    if success:
        version = licenses['licenseListVersion']
    else:
        logger.info(f'Fail to get spdx license list version:{error_msg}')
    return version


def write_spdx(output_file_without_ext, output_extension, sheet_list,
               scanner_name, scanner_version, spdx_version=(2, 3)):
    success = True
    error_msg = ''
    if sheet_list:
        doc = Document(version=Version(*spdx_version),
                       data_license=License.from_identifier('CC0-1.0'),
                       namespace=f'http://spdx.org/spdxdocs/{scanner_name.lower()}-{uuid.uuid4()}',
                       name=f'SPDX Document by {scanner_name.upper()}',
                       spdx_id='SPDXRef-DOCUMENT')

        doc.creation_info.set_created_now()
        doc.creation_info.add_creator(Tool(f'{scanner_name.upper()} {scanner_version}'))
        doc.creation_info.license_list_version = Version(*tuple(get_license_list_version().split('.')))

        relation_tree = {}
        spdx_id_packages = []

        output_dir = os.path.dirname(output_file_without_ext)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        try:
            package_id = 0
            root_package = False
            for sheet_name, sheet_contents in sheet_list.items():
                if sheet_name not in constant.supported_sheet_and_scanner.keys():
                    continue
                scanner = constant.supported_sheet_and_scanner.get(sheet_name)
                for oss_item in sheet_contents:
                    if len(oss_item) < 9:
                        logger.warning(f"sheet list is too short ({len(oss_item)}): {oss_item}")
                        continue
                    package_id += 1
                    package = Package(spdx_id=f'SPDXRef-{package_id}')

                    if oss_item[1] != '':
                        package.name = oss_item[1]  # required
                    else:
                        package.name = SPDXNone()

                    if oss_item[2] != '':
                        package.version = oss_item[2]  # no required

                    if oss_item[4] != '':
                        package.download_location = oss_item[4]  # required
                    else:
                        package.download_location = SPDXNone()

                    if scanner == constant.FL_DEPENDENCY:
                        package.files_analyzed = False  # If omitted, the default value of true is assumed.
                    else:
                        package.files_analyzed = True

                    if oss_item[5] != '':
                        package.homepage = oss_item[5]  # no required

                    if oss_item[6] != '':
                        package.cr_text = oss_item[3]  # required
                    else:
                        package.cr_text = SPDXNone()
                    if oss_item[3] != '':
                        lic_list = [check_input_license_format(lic.strip()) for lic in oss_item[3].split(',')]
                        package.license_declared = ','.join(lic_list)
                    else:
                        package.license_declared = NoAssert()  # required

                    doc.add_package(package)

                    if scanner == constant.FL_DEPENDENCY:
                        spdx_id_packages.append([package.name, package.spdx_id])
                        comment = oss_item[8]
                        relation_tree[package.name] = {}
                        relation_tree[package.name]['id'] = package.spdx_id
                        relation_tree[package.name]['dep'] = []

                        if 'root package' in comment.split(','):
                            root_package = True
                            relationship = Relationship(f"{doc.spdx_id} DESCRIBES {package.spdx_id}")
                            doc.add_relationships(relationship)
                        if len(oss_item) > 9:
                            deps = oss_item[9]
                            relation_tree[package.name]['dep'].extend([di.strip().split('(')[0] for di in deps.split(',')])
            if scanner == constant.FL_DEPENDENCY and len(relation_tree) > 0:
                for pkg in relation_tree:
                    if len(relation_tree[pkg]['dep']) > 0:
                        pkg_spdx_id = relation_tree[pkg]['id']
                        if len(relation_tree[pkg]['dep']) > 0:
                            for pname in relation_tree[pkg]['dep']:
                                ans = next(filter(lambda x: x[0] == pname, spdx_id_packages), None)
                                if ans is None:
                                    continue
                                rel_pkg_spdx_id = ans[1]
                                relationship = Relationship(f'{pkg_spdx_id} DEPENDS_ON {rel_pkg_spdx_id}')
                                doc.add_relationships(relationship)
                if not root_package:
                    root_package = Package(spdx_id='SPDXRef-ROOT-PACKAGE')
                    root_package.name = 'root package'
                    root_package.download_location = NoAssert()
                    root_package.files_analyzed = False
                    root_package.cr_text = SPDXNone()
                    root_package.license_declared = NoAssert()
                    doc.add_package(root_package)
                    relationship = Relationship(f"{doc.spdx_id} DESCRIBES {root_package.spdx_id}")
                    doc.add_relationships(relationship)
        except Exception as e:
            success = False
            error_msg = f'Failed to create spdx document object:{e}, {traceback.format_exc()}'
    else:
        success = False
        error_msg = 'No item to write in output file.'

    result_file = ''
    if success:
        result_file = output_file_without_ext + output_extension
        try:
            out_mode = "w"
            if result_file.endswith(".tag"):
                writer_module = tagvalue
            elif result_file.endswith(".json"):
                writer_module = json
            elif result_file.endswith(".xml"):
                writer_module = xml
            elif result_file.endswith(".yaml"):
                writer_module = yaml
            else:
                raise Exception("FileType Not Supported")

            with open(result_file, out_mode) as out:
                writer_module.write_document(doc, out, False)
        except Exception as e:
            success = False
            error_msg = f'Failed to write spdx document: {e}'
            if os.path.exists(result_file):
                os.remove(result_file)

    return success, error_msg, result_file


def convert_to_spdx_style(input_string):
    input_string = re.sub(r'[^\w\s\.\-]', '', input_string)
    input_string = re.sub(r'[\s\_]', '-', input_string)
    input_converted = f"LicenseRef-{input_string}"
    return input_converted


def check_input_license_format(input_license):
    spdx_licenses = get_spdx_licensename()
    for spdx in spdx_licenses:
        if input_license.casefold() == spdx.casefold():
            return spdx

    if input_license.startswith('LicenseRef-'):
        return input_license

    licensesfromJson = get_license_from_nick()
    if licensesfromJson == "":
        logger.warning(" Error - Return Value to get license from Json is none")

    try:
        converted_license = licensesfromJson.get(input_license.casefold())
        if converted_license is None:
            converted_license = convert_to_spdx_style(input_license)
    except Exception as ex:
        logger.warning(f"Error - Get frequetly used license : {ex}")

    return converted_license


def get_spdx_licensename():
    spdx_licenses = []
    try:
        success, error_msg, licenses = get_spdx_licenses_json()
        if success is False:
            logger.warning(f"Error to get SPDX Licesens : {error_msg}")

        licenseInfo = licenses.get("licenses")
        for info in licenseInfo:
            shortID = info.get("licenseId")
            isDeprecated = info.get("isDeprecatedLicenseId")
            if isDeprecated is False:
                spdx_licenses.append(shortID)
    except Exception as ex:
        logger.warning(f"Error access to get_spdx_licenses_json : {ex}")
    return spdx_licenses
