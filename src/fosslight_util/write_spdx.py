#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import uuid
import logging
import re
from pathlib import Path
from datetime import datetime
from fosslight_util.spdx_licenses import get_spdx_licenses_json, get_license_from_nick
from fosslight_util.constant import (LOGGER_NAME, FOSSLIGHT_DEPENDENCY, FOSSLIGHT_SCANNER,
                                     FOSSLIGHT_BINARY, FOSSLIGHT_SOURCE)
from fosslight_util.oss_item import CHECKSUM_NULL, get_checksum_sha1
import traceback

logger = logging.getLogger(LOGGER_NAME)

try:
    from spdx_tools.common.spdx_licensing import spdx_licensing
    from spdx_tools.spdx.model import (
        Actor,
        ActorType,
        Checksum,
        ChecksumAlgorithm,
        CreationInfo,
        Document,
        File,
        Package,
        Relationship,
        RelationshipType,
        SpdxNoAssertion,
        SpdxNone
    )
    from spdx_tools.spdx.validation.document_validator import validate_full_spdx_document
    from spdx_tools.spdx.writer.write_anything import write_file
except Exception:
    logger.info('No import spdx-tools')


def get_license_list_version():
    version = 'N/A'
    success, error_msg, licenses = get_spdx_licenses_json()
    if success:
        version = licenses['licenseListVersion']
    else:
        logger.info(f'Fail to get spdx license list version:{error_msg}')
    return version


def write_spdx(output_file_without_ext, output_extension, scan_item, spdx_version='2.3'):
    success = True
    error_msg = ''

    if scan_item:
        try:
            cover_name = scan_item.cover.get_print_json()["Tool information"].split('(').pop(0).strip()
            match = re.search(r"(.+) v([0-9.]+)", cover_name)
            if match:
                scanner_name = match.group(1)
            else:
                scanner_name = FOSSLIGHT_SCANNER
        except Exception:
            cover_name = FOSSLIGHT_SCANNER
            scanner_name = FOSSLIGHT_SCANNER
        creation_info = CreationInfo(spdx_version=f'SPDX-{spdx_version}',
                                     spdx_id='SPDXRef-DOCUMENT',
                                     name=f'SPDX Document by {scanner_name.upper()}',
                                     data_license='CC0-1.0',
                                     document_namespace=f'http://spdx.org/spdxdocs/{scanner_name.lower()}-{uuid.uuid4()}',
                                     creators=[Actor(name=cover_name, actor_type=ActorType.TOOL)],
                                     created=datetime.now())
        doc = Document(creation_info=creation_info)

        relation_tree = {}
        spdx_id_packages = []

        output_dir = os.path.dirname(output_file_without_ext)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        try:
            file_id = 0
            package_id = 0
            root_package = False
            for scanner_name, file_items in scan_item.file_items.items():
                for file_item in file_items:
                    file = ''  # file의 license, copyright은 oss item에서 append
                    if scanner_name in [FOSSLIGHT_BINARY, FOSSLIGHT_SOURCE]:
                        if file_item.exclude:
                            continue
                        if file_item.checksum == CHECKSUM_NULL:
                            if os.path.exists(file_item.source_name_or_path):
                                file_item.checksum = get_checksum_sha1(file_item.source_name_or_path)
                            if file_item.checksum == CHECKSUM_NULL:
                                logger.info(f'Failed to get checksum, Skip: {file_item.source_name_or_path}')
                                continue
                        file_id += 1
                        file = File(name=file_item.source_name_or_path,
                                    spdx_id=f'SPDXRef-File{file_id}',
                                    checksums=[Checksum(ChecksumAlgorithm.SHA1, file_item.checksum)])
                    file_license = []
                    file_copyright = []
                    file_comment = []
                    for oss_item in file_item.oss_items:
                        oss_licenses = []
                        declared_oss_licenses = []
                        lic_comment = []
                        for oi in oss_item.license:
                            oi = check_input_license_format(oi)
                            try:
                                oi_spdx = spdx_licensing.parse(oi, validate=True)
                                oss_licenses.append(oi_spdx)
                                declared_oss_licenses.append(oi)
                            except Exception:
                                logger.debug(f'No spdx license name: {oi}')
                                lic_comment.append(oi)
                                file_comment.append(oi)
                        if oss_licenses:
                            file_license.extend(oss_licenses)
                        if oss_item.copyright != '':
                            file_copyright.append(oss_item.copyright)

                        if oss_item.download_location == '':
                            if scanner_name == FOSSLIGHT_DEPENDENCY:
                                download_location = SpdxNone()
                            else:
                                continue
                        else:
                            download_location = oss_item.download_location
                        if scanner_name != FOSSLIGHT_DEPENDENCY and oss_item.name == '':
                            continue
                        package_id += 1
                        package = Package(name=oss_item.name,
                                          spdx_id=f'SPDXRef-Package{package_id}',
                                          download_location=download_location)

                        if oss_item.version != '':
                            package.version = oss_item.version

                        if scanner_name == FOSSLIGHT_DEPENDENCY:
                            package.files_analyzed = False  # If omitted, the default value of true is assumed.
                        else:
                            package.files_analyzed = True
                        if oss_item.copyright != '':
                            package.cr_text = oss_item.copyright
                        if oss_item.homepage != '':
                            package.homepage = oss_item.homepage

                        if declared_oss_licenses:
                            package.license_declared = spdx_licensing.parse(' AND '.join(declared_oss_licenses))
                        if lic_comment:
                            package.license_comment = ' '.join(lic_comment)

                        doc.packages.append(package)

                        if scanner_name == FOSSLIGHT_DEPENDENCY:
                            purl = file_item.purl
                            spdx_id_packages.append([purl, package.spdx_id])
                            relation_tree[purl] = {}
                            relation_tree[purl]['id'] = package.spdx_id
                            relation_tree[purl]['dep'] = []
                            if 'root package' in oss_item.comment:
                                root_package = True
                                relationship = Relationship(doc.creation_info.spdx_id,
                                                            RelationshipType.DESCRIBES,
                                                            package.spdx_id)
                                doc.relationships.append(relationship)
                            relation_tree[purl]['dep'].extend(file_item.depends_on)

                    if scanner_name in [FOSSLIGHT_BINARY, FOSSLIGHT_SOURCE]:
                        if file_license:
                            file.license_info_in_file = file_license
                        if file_copyright:
                            file.copyright_text = '\n'.join(file_copyright)
                        if file_comment:
                            file.license_comment = ' '.join(file_comment)
                        doc.files.append(file)

            if len(doc.packages) > 0:
                for pkg in relation_tree:
                    if len(relation_tree[pkg]['dep']) > 0:
                        pkg_spdx_id = relation_tree[pkg]['id']
                        if len(relation_tree[pkg]['dep']) > 0:
                            for pname in relation_tree[pkg]['dep']:
                                ans = next(filter(lambda x: x[0] == pname, spdx_id_packages), None)
                                if ans is None:
                                    continue
                                rel_pkg_spdx_id = ans[1]
                                relationship = Relationship(pkg_spdx_id, RelationshipType.DEPENDS_ON, rel_pkg_spdx_id)
                                doc.relationships.append(relationship)
            if not root_package:
                root_package = Package(name='root package',
                                       spdx_id='SPDXRef-ROOT-PACKAGE',
                                       download_location=SpdxNoAssertion())
                root_package.files_analyzed = False
                root_package.license_declared = SpdxNoAssertion()
                doc.packages.append(root_package)
                relationship = Relationship(doc.creation_info.spdx_id, RelationshipType.DESCRIBES, root_package.spdx_id)
                doc.relationships.append(relationship)

        except Exception as e:
            success = False
            error_msg = f'Failed to create spdx document object:{e}, {traceback.format_exc()}'
    else:
        success = False
        error_msg = 'No item to write in output file.'

    validation_messages = validate_full_spdx_document(doc)
    for message in validation_messages:
        logger.warning(message.validation_message)
        logger.warning(message.context)

    # assert validation_messages == []

    result_file = ''
    if success:
        result_file = output_file_without_ext + output_extension
        try:
            write_file(doc, result_file)
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
