#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 LG Electronics Inc.
# Copyright (c) OWASP Foundation.
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import re
from pathlib import Path
from fosslight_util.constant import (FOSSLIGHT_BINARY, FOSSLIGHT_DEPENDENCY, FOSSLIGHT_SCANNER,
                                     FOSSLIGHT_SOURCE, LOGGER_NAME)
import traceback

logger = logging.getLogger(LOGGER_NAME)

_SCANNER_TOOL_NAMES = {
    FOSSLIGHT_SCANNER: 'FOSSLIGHT_SCANNER',
    FOSSLIGHT_DEPENDENCY: 'FOSSLIGHT_Dependency',
    FOSSLIGHT_SOURCE: 'FOSSLIGHT_Source',
    FOSSLIGHT_BINARY: 'FOSSLIGHT_Binary',
}
_SCANNER_TOOL_PATTERN = re.compile(r'^(?P<name>[A-Za-z0-9_-]+)\s+v(?P<version>[^\s(]+)')


def _get_scanner_tool_components(scanner_covers):
    scanner_versions = {}
    for cover in scanner_covers:
        tool_name = getattr(cover, 'tool_name', '')
        if not tool_name and hasattr(cover, 'get_print_json'):
            tool_name = cover.get_print_json().get('Tool information', '')
        match = _SCANNER_TOOL_PATTERN.match(tool_name.strip())
        if match:
            scanner_name = match.group('name').lower()
            if scanner_name in _SCANNER_TOOL_NAMES:
                scanner_versions[scanner_name] = match.group('version')

    return [
        Component(name=_SCANNER_TOOL_NAMES[scanner_name],
                  type=ComponentType.APPLICATION,
                  group='FOSSLight',
                  version=scanner_versions[scanner_name])
        for scanner_name in _SCANNER_TOOL_NAMES
        if scanner_name in scanner_versions
    ]

_cyclonedx_import_error = None
try:
    from packageurl import PackageURL
    from cyclonedx.builder.this import this_component as cdx_lib_component
    from cyclonedx.exception import MissingOptionalDependencyException
    from cyclonedx.factory.license import LicenseFactory
    from cyclonedx.model import XsUri, ExternalReferenceType
    from cyclonedx.model.bom import Bom
    from cyclonedx.model.component import (Component, ComponentType, ExternalReference, HashAlgorithm,
                                           HashType, Property)
    from cyclonedx.output import make_outputter, BaseOutput
    from cyclonedx.output.json import JsonV1Dot6
    from cyclonedx.schema import OutputFormat, SchemaVersion
    from cyclonedx.validation.json import JsonStrictValidator
    from cyclonedx.output.json import Json as JsonOutputter
    from cyclonedx.validation.xml import XmlValidator
except Exception as error:
    _cyclonedx_import_error = error
    logger.info(f'Failed to import cyclonedx-python-lib: {error}')


def write_cyclonedx(output_file_without_ext, output_extension, scan_item, scanner_covers=None):
    success = True
    error_msg = ''

    if _cyclonedx_import_error is not None:
        return False, f'Failed to import cyclonedx-python-lib: {_cyclonedx_import_error}', ''

    bom = Bom()
    if scan_item:
        lc_factory = LicenseFactory()
        bom.metadata.tools.components.add(cdx_lib_component())
        if scanner_covers is None:
            scanner_covers = [scan_item.cover]
        bom.metadata.tools.components.update(_get_scanner_tool_components(scanner_covers))
        comp_id = 0
        input_path = getattr(scan_item.cover, "input_path", "")
        root_name = os.path.basename(os.path.normpath(input_path)) if input_path else ""
        if not root_name:
            root_name = "Root Component"
        bom.metadata.component = root_component = Component(name=root_name,
                                                            type=ComponentType.APPLICATION,
                                                            bom_ref=str(comp_id))
        relation_tree = {}

        output_dir = os.path.dirname(output_file_without_ext)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        try:
            root_package = False
            for scanner_name, file_items in scan_item.file_items.items():
                for file_item in file_items:
                    if file_item.exclude:
                        continue
                    if scanner_name in (FOSSLIGHT_SOURCE, FOSSLIGHT_BINARY):
                        comp_type = ComponentType.FILE
                    else:
                        comp_type = ComponentType.LIBRARY

                    for oss_item in file_item.oss_items:
                        if oss_item.name == '' or oss_item.name == '-':
                            comp_name = 'NOASSERTION'
                        else:
                            comp_name = oss_item.name

                        comp_id += 1
                        comp = Component(type=comp_type,
                                         name=comp_name,
                                         bom_ref=str(comp_id))

                        if oss_item.version != '':
                            comp.version = oss_item.version
                        if oss_item.copyright != '':
                            comp.copyright = oss_item.copyright
                        if scanner_name == FOSSLIGHT_DEPENDENCY and file_item.purl:
                            comp.purl = PackageURL.from_string(file_item.purl)
                        if scanner_name != FOSSLIGHT_DEPENDENCY:
                            if file_item.checksum != '0':
                                comp.hashes = [HashType(alg=HashAlgorithm.SHA_1, content=file_item.checksum)]
                        if scanner_name == FOSSLIGHT_BINARY:
                            tlsh = str(getattr(file_item, 'tlsh', '') or '').strip()
                            if tlsh and tlsh.upper() not in ('0', 'TNULL'):
                                comp.properties = [Property(name='fosslight:tlsh', value=tlsh)]

                        if oss_item.download_location != '':
                            comp.external_references = [ExternalReference(url=XsUri(oss_item.download_location),
                                                                          type=ExternalReferenceType.WEBSITE)]

                        oss_licenses = []
                        for ol in oss_item.license:
                            try:
                                oss_licenses.append(lc_factory.make_from_string(ol))
                            except Exception:
                                logger.info(f'No spdx license name: {ol}')
                        if oss_licenses:
                            comp.licenses = oss_licenses

                        root_package = False
                        if scanner_name == FOSSLIGHT_DEPENDENCY:
                            if oss_item.comment:
                                oss_comment = oss_item.comment.split('/')
                                for oc in oss_comment:
                                    if oc in ['direct', 'transitive', 'root package']:
                                        if oc == 'direct':
                                            bom.register_dependency(root_component, [comp])
                                        elif oc == 'root package':
                                            root_package = True
                                            comp_id -= 1
                            else:
                                bom.register_dependency(root_component, [comp])
                            if len(file_item.depends_on) > 0:
                                purl = file_item.purl
                                relation_tree[purl] = []
                                relation_tree[purl].extend(file_item.depends_on)

                        if not root_package:
                            bom.components.add(comp)

            if len(bom.components) > 0:
                for comp_purl in relation_tree:
                    comp = bom.get_component_by_purl(PackageURL.from_string(comp_purl))
                    if comp:
                        dep_comp_list = []
                        for dep_comp_purl in relation_tree[comp_purl]:
                            dep_comp = bom.get_component_by_purl(PackageURL.from_string(dep_comp_purl))
                            if dep_comp:
                                dep_comp_list.append(dep_comp)
                        bom.register_dependency(comp, dep_comp_list)

        except Exception as e:
            success = False
            error_msg = f'Failed to create CycloneDX document object:{e}, {traceback.format_exc()}'
    else:
        success = False
        error_msg = 'No item to write in output file.'

    result_file = ''
    if success:
        result_file = output_file_without_ext + output_extension
        try:
            if output_extension == '.json':
                success = write_cyclonedx_json(bom, result_file)
            elif output_extension == '.xml':
                success = write_cyclonedx_xml(bom, result_file)
            else:
                success = False
                error_msg = f'Not supported output_extension({output_extension})'
            if not success and not error_msg:
                error_msg = f'Failed to write CycloneDX document: {result_file}'
        except Exception as e:
            success = False
            error_msg = f'Failed to write CycloneDX document: {e}'
        if not success and os.path.exists(result_file):
            os.remove(result_file)

    return success, error_msg, result_file


def write_cyclonedx_json(bom, result_file):
    success = True
    try:
        my_json_outputter: 'JsonOutputter' = JsonV1Dot6(bom)
        my_json_outputter.output_to_file(result_file)
        serialized_json = my_json_outputter.output_as_string(indent=2)
        my_json_validator = JsonStrictValidator(SchemaVersion.V1_6)
        try:
            validation_errors = my_json_validator.validate_str(serialized_json)
            if validation_errors:
                logger.warning(f'JSON invalid, ValidationError: {repr(validation_errors)}')
        except MissingOptionalDependencyException as error:
            logger.debug(f'JSON-validation was skipped due to {error}')
    except Exception as e:
        logger.warning(f'Fail to write cyclonedx json: {e}')
        success = False
    return success


def write_cyclonedx_xml(bom, result_file):
    success = True
    try:
        my_xml_outputter: BaseOutput = make_outputter(bom=bom,
                                                      output_format=OutputFormat.XML,
                                                      schema_version=SchemaVersion.V1_6)
        my_xml_outputter.output_to_file(filename=result_file)
        serialized_xml = my_xml_outputter.output_as_string(indent=2)
        my_xml_validator = XmlValidator(SchemaVersion.V1_6)
        try:
            validation_errors = my_xml_validator.validate_str(serialized_xml)
            if validation_errors:
                logger.warning(f'XML invalid, ValidationError: {repr(validation_errors)}')
        except MissingOptionalDependencyException as error:
            logger.debug(f'XML-validation was skipped due to {error}')
    except Exception as e:
        logger.warning(f'Fail to write cyclonedx xml: {e}')
        success = False
    return success
