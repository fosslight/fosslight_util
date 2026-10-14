#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import hashlib
import json
import logging
import ntpath
import os
import re
import uuid
from collections import defaultdict
from importlib.metadata import version as package_version
from pathlib import Path
from datetime import datetime, timezone
from fosslight_util.spdx_licenses import get_spdx_licenses_json, get_license_from_nick
from fosslight_util.constant import (LOGGER_NAME, FOSSLIGHT_DEPENDENCY, FOSSLIGHT_SCANNER,
                                     FOSSLIGHT_BINARY, FOSSLIGHT_SOURCE)
from fosslight_util.oss_item import get_checksum_sha1

logger = logging.getLogger(LOGGER_NAME)
_spdx_import_error = None

try:
    from packageurl import PackageURL
    from spdx_tools.common.spdx_licensing import spdx_licensing
    from spdx_tools.spdx.jsonschema.document_converter import DocumentConverter
    from spdx_tools.spdx.jsonschema.external_package_ref_converter import ExternalPackageRefConverter
    from spdx_tools.spdx.model import (
        Actor,
        ActorType,
        Checksum,
        ChecksumAlgorithm,
        CreationInfo,
        Document,
        ExternalPackageRef,
        ExternalPackageRefCategory,
        ExtractedLicensingInfo,
        File,
        FileType,
        Package,
        Relationship,
        RelationshipType,
        SpdxNoAssertion,
        SpdxNone
    )
    from spdx_tools.spdx.validation.document_validator import validate_full_spdx_document
    from spdx_tools.spdx.writer.json import json_writer
    from spdx_tools.spdx.writer.write_anything import write_file
    from spdx_tools.spdx.writer.xml import xml_writer
    from spdx_tools.spdx.writer.yaml import yaml_writer
except Exception as error:
    _spdx_import_error = error
    logger.info('No import spdx-tools')


def get_license_list_version():
    version = 'N/A'
    success, error_msg, licenses = get_spdx_licenses_json()
    if success:
        version = licenses['licenseListVersion']
    else:
        logger.info(f'Fail to get spdx license list version:{error_msg}')
    return version


def write_spdx(output_file_without_ext, output_extension, scan_item, spdx_version='2.3', scanner_covers=None):
    if _spdx_import_error is not None:
        return False, f'Failed to import spdx-tools: {_spdx_import_error}', ''
    if not scan_item:
        return False, 'No item to write in output file.', ''
    result_file = ''
    try:
        document = Document(creation_info=_creation_info(scan_item, scanner_covers))
        root = Package(
            name=document.creation_info.name, spdx_id=_ROOT_PACKAGE_ID,
            download_location=SpdxNoAssertion(), files_analyzed=False
        )
        document.packages.append(root)
        seen_relationships = set()
        _add_relationship(document, seen_relationships, 'SPDXRef-DOCUMENT', RelationshipType.DESCRIBES, root.spdx_id)
        package_ids_by_purl = defaultdict(list)
        dependency_rows = []
        root_purls = set()
        checksums = {}
        registry = _LicenseRegistry()
        for scanner_name, file_items in scan_item.file_items.items():
            if scanner_name not in (FOSSLIGHT_DEPENDENCY, FOSSLIGHT_SOURCE, FOSSLIGHT_BINARY):
                continue
            is_dependency = scanner_name == FOSSLIGHT_DEPENDENCY
            for file_item in file_items:
                if file_item.exclude:
                    continue
                oss_items = [oss_item for oss_item in file_item.oss_items if not oss_item.exclude]
                if file_item.oss_items and not oss_items:
                    continue
                file_info = None if is_dependency else _file_info(
                    file_item, scan_item.cover.input_path, scanner_name, f'SPDXRef-File{len(document.files) + 1}', checksums
                )
                if file_info:
                    for oss_item in oss_items:
                        file_info.license_info_in_file.extend(
                            registry.licenses(oss_item.license, getattr(oss_item, 'license_texts', None))
                        )
                    file_info.license_info_in_file = _unique_licenses(file_info.license_info_in_file)
                    copyright_lines = {
                        line for oss_item in oss_items if oss_item.copyright != '-'
                        for line in oss_item.copyright.splitlines() if line
                    }
                    file_info.copyright_text = '\n'.join(sorted(copyright_lines)) or None
                    document.files.append(file_info)
                    _add_relationship(document, seen_relationships, 'SPDXRef-DOCUMENT', RelationshipType.DESCRIBES,
                                      file_info.spdx_id)
                for oss_item in oss_items:
                    classification = oss_item.comment
                    purl = _normalized_purl(getattr(file_item, 'purl', '')) if is_dependency else ''
                    if is_dependency and re.search(r'\broot package\b', classification, re.IGNORECASE):
                        package = root
                    else:
                        name = '' if oss_item.name == '-' else oss_item.name
                        download_location = '' if oss_item.download_location == '-' else oss_item.download_location
                        version = '' if oss_item.version == '-' else oss_item.version
                        copyright_text = '' if oss_item.copyright == '-' else oss_item.copyright
                        if not is_dependency and not name and not download_location:
                            continue
                        if download_location in ('NONE', 'NOASSERTION', ''):
                            download_location = SpdxNone() if download_location == 'NONE' else SpdxNoAssertion()
                        package = Package(
                            name=name or 'NOASSERTION', spdx_id=f'SPDXRef-Package{len(document.packages)}',
                            download_location=download_location, version=version or None,
                            homepage=oss_item.homepage or None, copyright_text=copyright_text or None,
                            files_analyzed=not is_dependency
                        )
                        if is_dependency:
                            licenses = registry.licenses(oss_item.license, getattr(oss_item, 'license_texts', None))
                            package.license_declared = (
                                spdx_licensing.parse(' AND '.join(f'({value})' for value in licenses)) if len(licenses) > 1
                                else licenses[0] if licenses else SpdxNone()
                            )
                        document.packages.append(package)
                        _add_relationship(document, seen_relationships, 'SPDXRef-DOCUMENT', RelationshipType.DESCRIBES,
                                          package.spdx_id)
                        if file_info:
                            _add_relationship(document, seen_relationships, package.spdx_id, RelationshipType.CONTAINS,
                                              file_info.spdx_id)
                    if is_dependency:
                        if purl:
                            if package.spdx_id not in package_ids_by_purl[purl]:
                                package_ids_by_purl[purl].append(package.spdx_id)
                            if package is not root or purl not in root_purls:
                                package.external_references.append(ExternalPackageRef(
                                    ExternalPackageRefCategory.PACKAGE_MANAGER, 'purl', purl
                                ))
                            if package is root:
                                root_purls.add(purl)
                        depends_on = getattr(file_item, 'depends_on', []) or []
                        dependency_rows.append((package.spdx_id, [depends_on] if isinstance(depends_on, str) else depends_on))
                        if package is not root and re.search(r'\bdirect\b', classification, re.IGNORECASE):
                            _add_relationship(document, seen_relationships, root.spdx_id, RelationshipType.DEPENDS_ON,
                                              package.spdx_id)
        for source, dependencies in dependency_rows:
            for dependency in dependencies:
                for target in package_ids_by_purl.get(_normalized_purl(dependency), []):
                    _add_relationship(document, seen_relationships, source, RelationshipType.DEPENDS_ON, target)
        registry.finalize(document)
        _populate_package_licenses(document)
        messages = validate_full_spdx_document(document)
        if messages:
            return False, 'Failed to validate SPDX document: ' + '; '.join(
                message.validation_message for message in messages
            ), ''
        result_file = str(output_file_without_ext) + output_extension
        Path(result_file).parent.mkdir(parents=True, exist_ok=True)
        if output_extension == '.tag':
            write_file(document, result_file, validate=False)
        else:
            class _ExternalRefConverter(ExternalPackageRefConverter):
                def convert(self, external_ref, document=None):
                    converted = super().convert(external_ref, document)
                    converted['referenceCategory'] = converted['referenceCategory'].replace('_', '-')
                    return converted

            converter = DocumentConverter()
            converter.package_converter.external_package_ref_converter = _ExternalRefConverter()
            writer = {'.json': json_writer, '.yaml': yaml_writer, '.xml': xml_writer}[output_extension]
            writer.write_document_to_file(document, result_file, validate=False, converter=converter, drop_duplicates=False)
        return True, '', result_file
    except Exception as error:
        logger.debug('Failed to create or write SPDX document', exc_info=True)
        if result_file and os.path.isfile(result_file):
            os.remove(result_file)
        return False, f'Failed to create or write SPDX document: {error}', result_file


_SCANNER_TOOL_NAMES = {
    FOSSLIGHT_SCANNER: 'FOSSLIGHT_SCANNER',
    FOSSLIGHT_DEPENDENCY: 'FOSSLIGHT_Dependency',
    FOSSLIGHT_SOURCE: 'FOSSLIGHT_Source',
    FOSSLIGHT_BINARY: 'FOSSLIGHT_Binary',
}
_TOOL_PATTERN = re.compile(r'^([A-Za-z0-9_-]+)\s+v([^\s(]+)')
_SHA1_PATTERN = re.compile(r'^[0-9a-fA-F]{40}$')
_TLSH_PATTERN = re.compile(r'^(?:T1)?[0-9a-f]{70}$', re.IGNORECASE)
_ROOT_PACKAGE_ID = 'SPDXRef-ROOT-PACKAGE'


def _tool(cover):
    tool_name = getattr(cover, 'tool_name', '')
    if not tool_name and hasattr(cover, 'get_print_json'):
        tool_name = cover.get_print_json().get('Tool information', '')
    return _TOOL_PATTERN.match(tool_name.strip())


def _unique_licenses(licenses):
    return list({str(license_value): license_value for license_value in sorted(licenses, key=str)}.values())


class _LicenseRegistry:
    def __init__(self):
        self.aliases = get_license_from_nick() or {}
        self.parsed = {}
        self.references = {}

    def _reference(self, name, texts):
        text = texts.get(name, '') or ''
        identity = (name, text)
        if identity not in self.references:
            self.references[identity] = spdx_licensing.parse(f'LicenseRef-FOSSLight-Internal{len(self.references) + 1}')
        return self.references[identity]

    def licenses(self, values, texts=None):
        texts = texts or {}
        result = []
        for value in [values] if isinstance(values, str) else values:
            if not value or value == '-':
                continue
            if value in ('NONE', 'NOASSERTION'):
                result.append(SpdxNone() if value == 'NONE' else SpdxNoAssertion())
                continue
            canonical = self.aliases.get(value.casefold(), value)
            try:
                if canonical not in self.parsed:
                    self.parsed[canonical] = spdx_licensing.parse(canonical)
                expression = self.parsed[canonical]
            except Exception:
                result.append(self._reference(value, texts))
                continue
            replacements = {}
            for symbol in spdx_licensing.license_symbols(expression, unique=True, decompose=True):
                if symbol.key not in spdx_licensing.known_symbols:
                    alias = self.aliases.get(symbol.key.casefold())
                    replacements[symbol] = spdx_licensing.parse(alias) if alias else self._reference(symbol.key, texts)
            result.append(expression.subs(replacements) if replacements else expression)
        return _unique_licenses(result)

    def finalize(self, document):
        groups = defaultdict(list)
        for identity, expression in self.references.items():
            name = re.sub(r'[\s_(]+', '-', identity[0].removeprefix('LicenseRef-'))
            identifier = re.sub(r'[^A-Za-z0-9.\-]', '', convert_to_spdx_style(name))
            groups[identifier].append((identity, expression))
        used_ids = {base for base, entries in groups.items() if base != 'LicenseRef-' and len(entries) == 1}
        replacements = {}
        definitions = []
        for base, entries in sorted(groups.items()):
            for (name, text), expression in sorted(entries, key=lambda entry: entry[0]):
                identifier = base
                if base == 'LicenseRef-' or len(entries) > 1:
                    digest = hashlib.sha256(json.dumps([name, text], ensure_ascii=False).encode('utf-8')).hexdigest()
                    for length in range(8, 65, 4):
                        identifier = f"{base}{'' if base == 'LicenseRef-' else '-'}{digest[:length]}"
                        if identifier not in used_ids:
                            break
                    else:
                        raise ValueError('Could not assign a unique LicenseRef identifier')
                used_ids.add(identifier)
                replacements[expression] = spdx_licensing.parse(identifier)
                definitions.append(ExtractedLicensingInfo(
                    license_id=identifier, extracted_text=text or name, license_name=name
                ))
        for file_info in document.files:
            file_info.license_info_in_file = [
                value.subs(replacements) if hasattr(value, 'subs') else value
                for value in file_info.license_info_in_file
            ]
        for package in document.packages:
            if hasattr(package.license_declared, 'subs'):
                package.license_declared = package.license_declared.subs(replacements)
        document.extracted_licensing_info = sorted(definitions, key=lambda definition: definition.license_id)


def _creation_info(scan_item, scanner_covers):
    input_path = scan_item.cover.input_path
    path_module = ntpath if ntpath.splitdrive(input_path)[0] else os.path
    document_name = path_module.basename(path_module.normpath(path_module.abspath(input_path))) or 'Root Component'
    first_tool = _tool(scan_item.cover)
    scanner_name = first_tool.group(1).lower() if first_tool else FOSSLIGHT_SCANNER
    creators = []
    seen = set()
    for cover in [scan_item.cover] if scanner_covers is None else scanner_covers:
        match = _tool(cover)
        if not match:
            continue
        name = _SCANNER_TOOL_NAMES.get(match.group(1).lower())
        identity = (name, match.group(2))
        if name and identity not in seen:
            creators.append(Actor(ActorType.TOOL, f'{name} - {match.group(2)}'))
            seen.add(identity)
    creators.append(Actor(ActorType.TOOL, f"spdx-tools - {package_version('spdx-tools')}"))
    return CreationInfo(
        spdx_version='SPDX-2.3', spdx_id='SPDXRef-DOCUMENT', name=document_name, data_license='CC0-1.0',
        document_namespace=f'http://opensource.lge.com/spdxdocs/{scanner_name}-{uuid.uuid4()}',
        creators=creators, created=datetime.now(timezone.utc)
    )


def _file_info(file_item, input_path, scanner_name, identifier, checksums):
    name = file_item.source_name_or_path
    if not name or name.endswith(('/', '\\')):
        return None
    path_module = ntpath if ntpath.splitdrive(input_path)[0] else os.path
    name = name.replace('\\', '/')
    full_path = path_module.normpath(name if path_module.isabs(name) else path_module.join(input_path, name))
    try:
        relative_path = path_module.relpath(full_path, input_path).replace('\\', '/')
    except ValueError:
        return None
    if relative_path == '.' or os.path.isdir(full_path):
        return None
    checksum = file_item.checksum
    if not _SHA1_PATTERN.fullmatch(checksum):
        if full_path not in checksums:
            checksums[full_path] = get_checksum_sha1(full_path)
        checksum = checksums[full_path]
    if not _SHA1_PATTERN.fullmatch(checksum):
        logger.info(f'Failed to get SHA-1, skip File: {name}')
        return None
    tlsh = getattr(file_item, 'tlsh', '')
    comment = f'fosslight:tlsh={tlsh}' if scanner_name == FOSSLIGHT_BINARY and _TLSH_PATTERN.fullmatch(tlsh) else None
    return File(
        name=f'./{relative_path}', spdx_id=identifier,
        checksums=[Checksum(ChecksumAlgorithm.SHA1, checksum.lower())],
        file_types=[FileType.BINARY if scanner_name == FOSSLIGHT_BINARY else FileType.SOURCE], comment=comment
    )


def _normalized_purl(value):
    try:
        return str(PackageURL.from_string(value))
    except (TypeError, ValueError):
        return ''


def _add_relationship(document, seen, source, relation_type, target):
    identity = (source, relation_type, target)
    if source != target and identity not in seen:
        document.relationships.append(Relationship(source, relation_type, target))
        seen.add(identity)


def _populate_package_licenses(document):
    files = {file_info.spdx_id: file_info for file_info in document.files}
    licenses = defaultdict(list)
    for relationship in document.relationships:
        if relationship.relationship_type == RelationshipType.CONTAINS and relationship.related_spdx_element_id in files:
            licenses[relationship.spdx_element_id].extend(files[relationship.related_spdx_element_id].license_info_in_file)
    for package in document.packages:
        if package.files_analyzed:
            package.license_info_from_files = _unique_licenses(licenses[package.spdx_id]) or [SpdxNone()]


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
