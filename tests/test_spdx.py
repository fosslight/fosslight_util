#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
import re
import xml.etree.ElementTree as ElementTree
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest
import yaml
from spdx_tools.common.spdx_licensing import spdx_licensing
from spdx_tools.spdx.model import Checksum, ChecksumAlgorithm, File, Package, Relationship, RelationshipType, SpdxNoAssertion
from spdx_tools.spdx.parser.parse_anything import parse_file
from spdx_tools.spdx.validation.document_validator import validate_full_spdx_document

from fosslight_util import write_spdx as spdx_writer
from fosslight_util.constant import FOSSLIGHT_BINARY, FOSSLIGHT_DEPENDENCY, FOSSLIGHT_SCANNER, FOSSLIGHT_SOURCE
from fosslight_util.oss_item import FileItem, OssItem, ScannerItem
from fosslight_util.output_format import write_output_file


def _scan_item(tmp_path, scanner_name=FOSSLIGHT_SOURCE):
    scan_item = ScannerItem(scanner_name)
    scan_item.cover.tool_name = f"{scanner_name} v1.2.3"
    scan_item.set_cover_pathinfo(str(tmp_path / "project"), [])
    return scan_item


def _write_json(tmp_path, scan_item, scanner_covers=None):
    success, error, result_file = write_output_file(
        str(tmp_path / "report"), ".json", scan_item, format="spdx-json", scanner_covers=scanner_covers
    )
    assert success, error
    return json.loads(Path(result_file).read_text(encoding="utf-8"))


def _file(name, oss_items=(), checksum="a" * 40):
    file_item = FileItem("")
    file_item.source_name_or_path = name
    file_item.checksum = checksum
    file_item.oss_items.extend(oss_items)
    return file_item


def _dependency(name, purl="", depends_on=(), classification="", licenses=""):
    file_item = _file("manifest.json", [OssItem(name, "", licenses)])
    file_item.purl = purl
    file_item.depends_on = list(depends_on)
    file_item.oss_items[0].comment = classification
    return file_item


def _relationships(document, relationship_type):
    return {
        (relationship["spdxElementId"], relationship["relatedSpdxElement"])
        for relationship in document["relationships"]
        if relationship["relationshipType"] == relationship_type
    }


def test_empty_scan_has_named_document_and_root(tmp_path):
    success, error, result_file = write_output_file(
        str(tmp_path / "report"), ".json", _scan_item(tmp_path), format="spdx-json"
    )

    assert success, error
    document = json.loads(Path(result_file).read_text(encoding="utf-8"))
    assert document["name"] == "project"
    assert document["documentNamespace"].startswith("http://opensource.lge.com/spdxdocs/fosslight_source-")
    assert document["packages"] == [{
        "name": "project",
        "SPDXID": "SPDXRef-ROOT-PACKAGE",
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": False,
    }]
    assert document["relationships"] == [{
        "spdxElementId": "SPDXRef-DOCUMENT",
        "relationshipType": "DESCRIBES",
        "relatedSpdxElement": "SPDXRef-ROOT-PACKAGE",
    }]


def test_creators_use_executed_covers_and_deduplicate_by_name_and_version(tmp_path):
    scan_item = _scan_item(tmp_path, FOSSLIGHT_SCANNER)
    scan_item.cover.tool_name += " (fosslight_binary v9.9.9)"
    covers = [
        scan_item.cover,
        SimpleNamespace(tool_name="fosslight_source v1.2.3"),
        SimpleNamespace(tool_name="fosslight_source v1.2.3"),
        SimpleNamespace(tool_name="fosslight_source v2.0.0"),
    ]
    document = _write_json(tmp_path, scan_item, covers)

    assert set(document["creationInfo"]["creators"]) == {
        "Tool: FOSSLIGHT_SCANNER - 1.2.3",
        "Tool: FOSSLIGHT_Source - 1.2.3",
        "Tool: FOSSLIGHT_Source - 2.0.0",
        f"Tool: spdx-tools - {version('spdx-tools')}",
    }
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", document["creationInfo"]["created"])
    assert "licenseListVersion" not in document["creationInfo"]


def test_missing_spdx_tools_metadata_does_not_prevent_output(tmp_path, monkeypatch):
    def missing_version(distribution):
        raise PackageNotFoundError(distribution)

    monkeypatch.setattr(spdx_writer, "package_version", missing_version)
    document = _write_json(tmp_path, _scan_item(tmp_path))

    assert set(document["creationInfo"]["creators"]) == {
        "Tool: FOSSLIGHT_Source - 1.2.3",
        "Tool: spdx-tools - unknown",
    }


def test_file_is_shared_by_packages_and_supplies_their_full_license_set(tmp_path):
    scan_item = _scan_item(tmp_path)
    named_oss = OssItem("first", "-", "MIT")
    url_oss = OssItem("", "2.0", "Apache-2.0", "https://example.com/archive.tar.gz")
    excluded_oss = OssItem("excluded", "", "GPL-3.0-only")
    excluded_oss.exclude = True
    excluded_oss.copyright = "Excluded copyright"
    scan_item.append_file_items([_file("src/example.c", [named_oss, url_oss, excluded_oss], "A" * 40)])
    document = _write_json(tmp_path, scan_item)

    assert len(document["files"]) == 1
    file_info = document["files"][0]
    assert file_info["fileName"] == "./src/example.c"
    assert file_info["fileTypes"] == ["SOURCE"]
    assert file_info["checksums"] == [{"algorithm": "SHA1", "checksumValue": "a" * 40}]
    assert set(file_info["licenseInfoInFiles"]) == {"MIT", "Apache-2.0"}
    assert "copyrightText" not in file_info
    packages = document["packages"][1:]
    assert [package["name"] for package in packages] == ["first", "NOASSERTION"]
    assert "versionInfo" not in packages[0]
    assert packages[0]["downloadLocation"] == "NOASSERTION"
    for package in packages:
        assert package["filesAnalyzed"] is True
        assert "licenseDeclared" not in package
        assert "licenseConcluded" not in package
        assert set(package["licenseInfoFromFiles"]) == {"MIT", "Apache-2.0"}
    assert _relationships(document, "CONTAINS") == {
        (package["SPDXID"], file_info["SPDXID"]) for package in packages
    }
    assert len(_relationships(document, "DESCRIBES")) == 4


def test_dependency_roots_and_duplicate_purls_keep_all_targets(tmp_path):
    scan_item = _scan_item(tmp_path, FOSSLIGHT_DEPENDENCY)
    target_purl = "pkg:npm/target@1.0"
    other_purl = "pkg:npm/other@2.0"
    scan_item.append_file_items([
        _dependency("root-a", "pkg:npm/root-a@1", [target_purl], "root package"),
        _dependency("root-b", "pkg:npm/root-b@1", [other_purl], "root package"),
        _dependency("first", target_purl, [other_purl, target_purl, "invalid"], "direct", ["MIT", "Apache-2.0"]),
        _dependency("second", target_purl, [], "transitive", "MIT"),
        _dependency("other", other_purl, [], "transitive"),
    ])
    document = _write_json(tmp_path, scan_item)

    assert len(document["packages"]) == 4
    assert not document.get("files")
    root, first, second, other = document["packages"]
    assert root["name"] == "project"
    assert root["SPDXID"] == "SPDXRef-ROOT-PACKAGE"
    assert root["filesAnalyzed"] is False
    assert "licenseDeclared" not in root
    assert "licenseInfoFromFiles" not in first
    assert first["licenseDeclared"] in {"MIT AND Apache-2.0", "Apache-2.0 AND MIT"}
    assert other["licenseDeclared"] == "NONE"
    assert first["externalRefs"] == [{
        "referenceCategory": "PACKAGE-MANAGER",
        "referenceType": "purl",
        "referenceLocator": target_purl,
    }]
    assert _relationships(document, "DEPENDS_ON") == {
        (root["SPDXID"], first["SPDXID"]),
        (root["SPDXID"], second["SPDXID"]),
        (root["SPDXID"], other["SPDXID"]),
        (first["SPDXID"], second["SPDXID"]),
        (first["SPDXID"], other["SPDXID"]),
    }


def test_direct_dependency_does_not_require_purl_or_name(tmp_path):
    scan_item = _scan_item(tmp_path, FOSSLIGHT_DEPENDENCY)
    scan_item.append_file_items([
        _dependency("-", "", ["invalid"], "direct"),
        _dependency("unclassified"),
        _dependency("indirect", "pkg:npm/indirect@1", [], "transitive"),
    ])
    document = _write_json(tmp_path, scan_item)

    direct = document["packages"][1]
    assert direct["name"] == "NOASSERTION"
    assert direct["downloadLocation"] == "NOASSERTION"
    assert direct["licenseDeclared"] == "NONE"
    assert "externalRefs" not in direct
    assert _relationships(document, "DEPENDS_ON") == {("SPDXRef-ROOT-PACKAGE", direct["SPDXID"])}


def test_invalid_checksum_omits_file_but_preserves_package(tmp_path):
    scan_item = _scan_item(tmp_path)
    scan_item.append_file_items([_file("missing.c", [OssItem("package", "", "MIT")], "invalid")])
    document = _write_json(tmp_path, scan_item)

    assert not document.get("files")
    assert len(document["packages"]) == 2
    assert document["packages"][1]["licenseInfoFromFiles"] == ["NONE"]
    assert not _relationships(document, "CONTAINS")


@pytest.mark.parametrize("scanner_name", [FOSSLIGHT_SOURCE, FOSSLIGHT_DEPENDENCY])
def test_legacy_oss_without_license_texts_remains_supported(tmp_path, scanner_name):
    scan_item = _scan_item(tmp_path, scanner_name)
    oss_item = OssItem("legacy", "1.0", "MIT")
    del oss_item.license_texts
    scan_item.append_file_items([_file("legacy.c", [oss_item])])

    document = _write_json(tmp_path, scan_item)

    package = document["packages"][1]
    assert package["name"] == "legacy"
    if scanner_name == FOSSLIGHT_DEPENDENCY:
        assert package["licenseDeclared"] == "MIT"
    else:
        assert package["licenseInfoFromFiles"] == ["MIT"]


def test_license_only_and_unmatched_files_are_independent_of_package_creation(tmp_path):
    scan_item = _scan_item(tmp_path)
    excluded_oss = OssItem("excluded", "", "GPL-3.0-only")
    excluded_oss.exclude = True
    excluded_file = _file("excluded.c", [OssItem("excluded-file", "", "ISC")])
    excluded_file.exclude = True
    scan_item.append_file_items([
        _file("LICENSE", [OssItem("", "", "MIT")]),
        _file("unknown.c"),
        _file("all-excluded.c", [excluded_oss]),
        excluded_file,
    ])
    document = _write_json(tmp_path, scan_item)

    assert len(document["packages"]) == 1
    assert [file_info["fileName"] for file_info in document["files"]] == ["./LICENSE", "./unknown.c"]
    assert document["files"][0]["licenseInfoInFiles"] == ["MIT"]
    assert "licenseInfoInFiles" not in document["files"][1]


def test_package_licenses_follow_all_contained_files_without_leaking_between_packages(tmp_path):
    success, error, result_file = spdx_writer.write_spdx(str(tmp_path / "report"), ".json", _scan_item(tmp_path))
    assert success, error
    document = parse_file(result_file)
    file_licenses = [("MIT",), ("MIT", "Apache-2.0"), ("BSD-3-Clause",), ("ISC",), ("MPL-2.0",)]
    for index, licenses in enumerate(file_licenses, start=1):
        file_info = File(
            name=f"./file{index}.c", spdx_id=f"SPDXRef-File{index}",
            checksums=[Checksum(ChecksumAlgorithm.SHA1, "a" * 40)],
            license_info_in_file=[spdx_licensing.parse(license_value) for license_value in licenses],
        )
        document.files.append(file_info)
        document.relationships.append(Relationship("SPDXRef-DOCUMENT", RelationshipType.DESCRIBES, file_info.spdx_id))
    for name, indexes in (("A", (1, 2)), ("B", (3, 4))):
        package = Package(name=name, spdx_id=f"SPDXRef-Package{name}", download_location=SpdxNoAssertion())
        document.packages.append(package)
        document.relationships.append(Relationship("SPDXRef-DOCUMENT", RelationshipType.DESCRIBES, package.spdx_id))
        document.relationships.extend(
            Relationship(package.spdx_id, RelationshipType.CONTAINS, f"SPDXRef-File{index}") for index in indexes
        )

    spdx_writer._populate_package_licenses(document)

    assert {str(value) for value in document.packages[1].license_info_from_files} == {"MIT", "Apache-2.0"}
    assert {str(value) for value in document.packages[2].license_info_from_files} == {"BSD-3-Clause", "ISC"}
    assert validate_full_spdx_document(document) == []


def test_unknown_license_keeps_original_name_and_detected_text(tmp_path):
    scan_item = _scan_item(tmp_path)
    license_name = "BSD-like License (example)"
    text = "This file is licensed under BSD-like License (example)."
    oss_item = OssItem("custom", "", [license_name, "MIT"])
    oss_item.license_texts[license_name] = text
    scan_item.append_file_items([_file("custom.c", [oss_item])])
    document = _write_json(tmp_path, scan_item)

    assert document["hasExtractedLicensingInfos"] == [{
        "licenseId": "LicenseRef-BSD-like-License-example",
        "extractedText": text,
        "name": license_name,
    }]
    assert set(document["files"][0]["licenseInfoInFiles"]) == {"MIT", "LicenseRef-BSD-like-License-example"}
    assert set(document["packages"][1]["licenseInfoFromFiles"]) == {"MIT", "LicenseRef-BSD-like-License-example"}
    assert "licenseComments" not in document["files"][0]


def test_license_ref_collisions_share_only_identical_name_and_text(tmp_path):
    scan_item = _scan_item(tmp_path)
    oss_items = []
    for name, text in (("Custom License", "first"), ("Custom_License", "first"),
                       ("Custom License", "second"), ("Custom License", "first")):
        oss_item = OssItem("package", "", name)
        oss_item.license_texts[name] = text
        oss_items.append(oss_item)
    excluded = OssItem("excluded", "", "Excluded License")
    excluded.exclude = True
    scan_item.append_file_items([_file("custom.c", [*oss_items, excluded])])
    document = _write_json(tmp_path, scan_item)

    definitions = document["hasExtractedLicensingInfos"]
    assert len(definitions) == 3
    assert {(definition["name"], definition["extractedText"]) for definition in definitions} == {
        ("Custom License", "first"), ("Custom_License", "first"), ("Custom License", "second")
    }
    assert all(re.fullmatch(r"LicenseRef-Custom-License-[0-9a-f]{8}", definition["licenseId"]) for definition in definitions)
    assert set(document["files"][0]["licenseInfoInFiles"]) == {definition["licenseId"] for definition in definitions}


def test_license_ref_extends_hash_suffix_when_prefix_collides(tmp_path, monkeypatch):
    scan_item = _scan_item(tmp_path)
    scan_item.append_file_items([_file("custom.c", [
        OssItem("first", "", "Custom License"), OssItem("second", "", "Custom_License"),
    ])])

    def digest(value):
        name, _text = json.loads(value)
        suffix = "a" if name == "Custom License" else "b"
        return SimpleNamespace(hexdigest=lambda: "12345678" + suffix * 56)

    monkeypatch.setattr(spdx_writer.hashlib, "sha256", digest)
    document = _write_json(tmp_path, scan_item)

    identifiers = {definition["licenseId"] for definition in document["hasExtractedLicensingInfos"]}
    assert len(identifiers) == 2
    assert all(re.fullmatch(r"LicenseRef-Custom-License-12345678[ab]{0,56}", identifier) for identifier in identifiers)


def test_empty_normalized_license_name_uses_hash_and_name_as_text(tmp_path):
    scan_item = _scan_item(tmp_path)
    license_name = "\ub77c\uc774\uc120\uc2a4"
    scan_item.append_file_items([_file("custom.c", [OssItem("custom", "", license_name)])])
    document = _write_json(tmp_path, scan_item)

    definition = document["hasExtractedLicensingInfos"][0]
    assert re.fullmatch(r"LicenseRef-[0-9a-f]{8}", definition["licenseId"])
    assert definition["name"] == license_name
    assert definition["extractedText"] == license_name


@pytest.mark.parametrize("name, expected", [
    ("Custom_License", "LicenseRef-Custom-License"),
    ("Custom(License)", "LicenseRef-CustomLicense"),
    ("LicenseRef-Custom", "LicenseRef-LicenseRef-Custom"),
    ("\ub77c\uc774\uc120\uc2a4", "LicenseRef-\ub77c\uc774\uc120\uc2a4"),
])
def test_public_license_helper_keeps_existing_behavior(name, expected):
    from fosslight_util.write_spdx import convert_to_spdx_style

    assert convert_to_spdx_style(name) == expected


def test_dependency_license_expression_preserves_or_within_and(tmp_path):
    scan_item = _scan_item(tmp_path, FOSSLIGHT_DEPENDENCY)
    scan_item.append_file_items([
        _dependency("compound", licenses=["MIT OR Apache-2.0", "BSD-3-Clause"]),
        _dependency("exception", licenses="GPL-2.0-only WITH Classpath-exception-2.0"),
    ])
    document = _write_json(tmp_path, scan_item)

    assert spdx_licensing.is_equivalent(
        document["packages"][1]["licenseDeclared"], "(MIT OR Apache-2.0) AND BSD-3-Clause"
    )
    assert document["packages"][2]["licenseDeclared"] == "GPL-2.0-only WITH Classpath-exception-2.0"
    assert "hasExtractedLicensingInfos" not in document


@pytest.mark.parametrize("licenses, expected", [
    (["MIT", "NONE"], "MIT"),
    (["MIT", "NOASSERTION"], "MIT"),
    (["MIT", "NONE", "NOASSERTION"], "MIT"),
    (["MIT OR Apache-2.0", "BSD-3-Clause", "NONE", "NOASSERTION"], "(MIT OR Apache-2.0) AND BSD-3-Clause"),
    (["GPL-2.0-only WITH Classpath-exception-2.0", "NONE"], "GPL-2.0-only WITH Classpath-exception-2.0"),
    (["Custom License", "NOASSERTION"], "LicenseRef-Custom-License"),
    (["NONE"], "NONE"),
    (["NOASSERTION"], "NOASSERTION"),
])
def test_dependency_license_declaration_preserves_real_expressions_and_standalone_special_values(tmp_path, licenses, expected):
    scan_item = _scan_item(tmp_path, FOSSLIGHT_DEPENDENCY)
    scan_item.append_file_items([_dependency("dependency", licenses=licenses)])

    document = _write_json(tmp_path, scan_item)

    assert spdx_licensing.is_equivalent(document["packages"][1]["licenseDeclared"], expected)


@pytest.mark.parametrize("license_value", ["NONE", "NOASSERTION"])
def test_explicit_file_license_sentinels_are_preserved(tmp_path, license_value):
    scan_item = _scan_item(tmp_path)
    scan_item.append_file_items([_file("example.c", [OssItem("package", "", license_value)])])
    document = _write_json(tmp_path, scan_item)

    assert document["files"][0]["licenseInfoInFiles"] == [license_value]
    assert document["packages"][1]["licenseInfoFromFiles"] == [license_value]
    assert "hasExtractedLicensingInfos" not in document


@pytest.mark.parametrize("format_name, extension", [
    ("spdx-json", ".json"), ("spdx-yaml", ".yaml"), ("spdx-xml", ".xml"), ("spdx-tag", ".tag"),
])
def test_all_formats_round_trip_the_same_mixed_scan(tmp_path, format_name, extension):
    scan_item = _scan_item(tmp_path, FOSSLIGHT_SCANNER)
    custom_oss = OssItem("custom", "", "Custom License")
    custom_oss.license_texts["Custom License"] = "Custom detected text."
    scan_item.append_file_items([_file("source.c", [custom_oss])], FOSSLIGHT_SOURCE)
    binary = _file("app.bin", [OssItem("binary", "", "ISC")])
    binary.tlsh = "T1" + "A" * 70
    scan_item.append_file_items([binary], FOSSLIGHT_BINARY)
    purl = "pkg:npm/dependency@1.0"
    scan_item.append_file_items([_dependency("dependency", purl, [], "direct", "MIT")], FOSSLIGHT_DEPENDENCY)
    covers = [scan_item.cover, *[
        SimpleNamespace(tool_name=f"{scanner_name} v1.2.3")
        for scanner_name in (FOSSLIGHT_SOURCE, FOSSLIGHT_BINARY, FOSSLIGHT_DEPENDENCY)
    ]]

    success, error, result_file = write_output_file(
        str(tmp_path / "mixed"), extension, scan_item, format=format_name, scanner_covers=covers
    )

    assert success, error
    parsed = parse_file(result_file)
    assert validate_full_spdx_document(parsed) == []
    assert parsed.creation_info.spdx_version == "SPDX-2.3"
    assert parsed.creation_info.name == "project"
    assert len(parsed.creation_info.creators) == 5
    assert len(parsed.packages) == 4
    assert len(parsed.files) == 2
    assert len(parsed.extracted_licensing_info) == 1
    assert parsed.files[1].comment == f"fosslight:tlsh={binary.tlsh}"
    assert {str(value) for value in parsed.packages[1].license_info_from_files} == {"LicenseRef-Custom-License"}
    if extension in (".json", ".yaml"):
        text = Path(result_file).read_text(encoding="utf-8")
        data = json.loads(text) if extension == ".json" else yaml.safe_load(text)
        assert data["packages"][3]["externalRefs"][0]["referenceCategory"] == "PACKAGE-MANAGER"
        assert "licenseConcluded" not in data["files"][0]
        assert "licenseConcluded" not in data["packages"][1]
        assert "licenseDeclared" not in data["packages"][1]
        assert "licenseListVersion" not in data["creationInfo"]
    elif extension == ".xml":
        root = ElementTree.parse(result_file).getroot()
        assert [element.text for element in root.iter("referenceCategory")] == ["PACKAGE-MANAGER"]
        assert not list(root.iter("licenseConcluded"))
    else:
        text = Path(result_file).read_text(encoding="utf-8")
        assert f"ExternalRef: PACKAGE-MANAGER purl {purl}" in text
        assert "LicenseConcluded:" not in text
        assert "LicenseListVersion:" not in text


@pytest.mark.parametrize("input_path, expected_name", [
    ("/", "Root Component"), ("C:\\", "Root Component"),
    ("C:\\work\\project\\", "project"), ("\\\\server\\share\\", "Root Component"),
])
def test_document_name_normalizes_filesystem_roots_and_windows_paths(tmp_path, input_path, expected_name):
    scan_item = _scan_item(tmp_path)
    scan_item.cover.input_path = input_path
    document = _write_json(tmp_path, scan_item)

    assert document["name"] == expected_name
    assert document["packages"][0]["name"] == expected_name


def test_namespace_changes_on_repeated_output_and_falls_back_without_valid_tool(tmp_path):
    scan_item = _scan_item(tmp_path)
    scan_item.cover.tool_name = "not a tool version"
    first = _write_json(tmp_path, scan_item)
    second = _write_json(tmp_path, scan_item)

    assert first["documentNamespace"] != second["documentNamespace"]
    for document in (first, second):
        namespace = document["documentNamespace"]
        prefix = "http://opensource.lge.com/spdxdocs/fosslight_scanner-"
        assert namespace.startswith(prefix)
        assert "#" not in namespace
        assert UUID(namespace[len(prefix):]).version == 4


def test_checksum_lookup_uses_analysis_path_and_does_not_mutate_input(tmp_path, monkeypatch):
    scan_item = _scan_item(tmp_path)
    source_path = Path(scan_item.cover.input_path) / "src" / "example.c"
    source_path.parent.mkdir(parents=True)
    contents = b"source contents\n"
    source_path.write_bytes(contents)
    file_item = _file("src\\example.c", [OssItem("package", "", "MIT")], "0")
    scan_item.append_file_items([file_item])
    monkeypatch.chdir(tmp_path)
    document = _write_json(tmp_path, scan_item)

    assert document["files"][0]["fileName"] == "./src/example.c"
    assert document["files"][0]["checksums"] == [{
        "algorithm": "SHA1", "checksumValue": hashlib.sha1(contents).hexdigest(),
    }]
    assert file_item.checksum == "0"
    assert file_item.source_name_or_path == "src\\example.c"


@pytest.mark.parametrize("name", ["", ".", "folder/"])
def test_unidentifiable_file_paths_do_not_remove_packages(tmp_path, name):
    scan_item = _scan_item(tmp_path)
    scan_item.append_file_items([_file(name, [OssItem("package", "", "MIT")])])
    document = _write_json(tmp_path, scan_item)

    assert not document.get("files")
    assert len(document["packages"]) == 2
    assert document["packages"][1]["licenseInfoFromFiles"] == ["NONE"]


@pytest.mark.parametrize("tlsh, expected_tlsh", [
    ("T1" + "A" * 70, "T1" + "A" * 70),
    ("A" * 70, "A" * 70),
    (" \tT1" + "A" * 70 + "\n", "T1" + "A" * 70),
    (" " + "A" * 70 + " ", "A" * 70),
    ("", None),
    (" \t\n", None),
    (None, None),
    ("0", None),
    ("TNULL", None),
    ("T1INVALID", None),
])
def test_binary_tlsh_is_separate_from_sha1_and_only_valid_values_are_written(tmp_path, tlsh, expected_tlsh):
    scan_item = _scan_item(tmp_path, FOSSLIGHT_BINARY)
    binary = _file("app.bin", [OssItem("binary", "", "MIT")])
    binary.tlsh = tlsh
    scan_item.append_file_items([binary])
    document = _write_json(tmp_path, scan_item)

    file_info = document["files"][0]
    assert file_info["fileTypes"] == ["BINARY"]
    assert file_info["checksums"] == [{"algorithm": "SHA1", "checksumValue": "a" * 40}]
    if expected_tlsh is not None:
        assert file_info["comment"] == f"fosslight:tlsh={expected_tlsh}"
    else:
        assert "comment" not in file_info
    assert binary.tlsh == tlsh


@pytest.mark.parametrize("name", ["-", " padded.c "])
def test_file_name_is_not_normalized_as_package_metadata(tmp_path, name):
    scan_item = _scan_item(tmp_path)
    scan_item.append_file_items([_file(name, [OssItem("package", "", "MIT")])])
    document = _write_json(tmp_path, scan_item)

    assert document["files"][0]["fileName"] == f"./{name}"


def test_same_name_and_version_in_different_files_are_not_merged(tmp_path):
    scan_item = _scan_item(tmp_path)
    scan_item.append_file_items([
        _file("first.c", [OssItem("package", "1.0", "MIT")]),
        _file("second.c", [OssItem("package", "1.0", "Apache-2.0")]),
    ])
    document = _write_json(tmp_path, scan_item)

    assert len(document["packages"]) == 3
    assert _relationships(document, "CONTAINS") == {
        ("SPDXRef-Package1", "SPDXRef-File1"), ("SPDXRef-Package2", "SPDXRef-File2"),
    }
    assert document["packages"][1]["licenseInfoFromFiles"] == ["MIT"]
    assert document["packages"][2]["licenseInfoFromFiles"] == ["Apache-2.0"]


def test_bare_output_filename_is_supported(tmp_path, monkeypatch):
    scan_item = _scan_item(tmp_path)
    monkeypatch.chdir(tmp_path)

    success, error, result_file = spdx_writer.write_spdx("bare", ".json", scan_item)

    assert success, error
    assert result_file == "bare.json"
    assert (tmp_path / result_file).is_file()


@pytest.mark.parametrize("call_style", ["three_positional", "four_positional", "keyword"])
def test_write_spdx_legacy_call_forms(tmp_path, call_style):
    output_path = str(tmp_path / "legacy")
    scan_item = _scan_item(tmp_path)
    if call_style == "three_positional":
        result = spdx_writer.write_spdx(output_path, ".json", scan_item)
    elif call_style == "four_positional":
        result = spdx_writer.write_spdx(output_path, ".json", scan_item, "2.3")
    else:
        result = spdx_writer.write_spdx(
            output_file_without_ext=output_path, output_extension=".json", scan_item=scan_item, spdx_version="2.3"
        )

    success, error, result_file = result
    assert success, error
    assert result_file == output_path + ".json"
    assert json.loads(Path(result_file).read_text(encoding="utf-8"))["spdxVersion"] == "SPDX-2.3"


def test_validation_failure_is_reported_without_creating_output(tmp_path, monkeypatch):
    monkeypatch.setattr(spdx_writer, "validate_full_spdx_document", lambda document: [
        SimpleNamespace(validation_message="invalid document")
    ])

    success, error, result_file = write_output_file(
        str(tmp_path / "invalid"), ".json", _scan_item(tmp_path), format="spdx-json"
    )

    assert success is False
    assert "invalid document" in error
    assert result_file == str(tmp_path / "invalid.json")
    assert not (tmp_path / "invalid.json").exists()


def test_failed_serialization_returns_output_path_and_removes_partial_file(tmp_path, monkeypatch):
    result_path = tmp_path / "report.json"

    def failed_write(document, file_name, **kwargs):
        Path(file_name).write_text("partial", encoding="utf-8")
        raise OSError("write failed")

    monkeypatch.setattr(spdx_writer.json_writer, "write_document_to_file", failed_write)
    success, error, result_file = write_output_file(
        str(tmp_path / "report"), ".json", _scan_item(tmp_path), format="spdx-json"
    )

    assert success is False
    assert "write failed" in error
    assert result_file == str(result_path)
    assert not result_path.exists()


def test_missing_input_returns_failure(tmp_path):
    success, error, result_file = spdx_writer.write_spdx(
        str(tmp_path / "invalid"), ".json", None
    )

    assert success is False
    assert error
    assert result_file == ""
    assert not (tmp_path / "invalid.json").exists()
