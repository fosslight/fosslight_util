# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import json
import os
import xml.etree.ElementTree as ElementTree
from types import SimpleNamespace

import pytest

from fosslight_util.output_format import write_output_file
from fosslight_util.constant import FOSSLIGHT_BINARY, FOSSLIGHT_DEPENDENCY, FOSSLIGHT_SCANNER, FOSSLIGHT_SOURCE
from fosslight_util.oss_item import FileItem, OssItem, ScannerItem
from fosslight_util.write_cyclonedx import write_cyclonedx
from tests import constants


def _get_tool_components(result_file, extension):
    if extension == ".json":
        with open(result_file, encoding="utf-8") as cyclonedx_file:
            components = json.load(cyclonedx_file)["metadata"]["tools"]["components"]
        return {
            component["name"]: component
            for component in components
            if component["name"].startswith("FOSSLIGHT_") or component["name"] == "cyclonedx-python-lib"
        }

    root = ElementTree.parse(result_file).getroot()
    metadata = next(element for element in root if element.tag.endswith("metadata"))
    tools = next(element for element in metadata if element.tag.endswith("tools"))
    components = {}
    for component in tools.iter():
        if component is tools or not component.tag.endswith("component"):
            continue
        name = next(element.text for element in component if element.tag.endswith("name"))
        values = {"name": name, "type": component.attrib.get("type")}
        for field in ("group", "version"):
            value = next((element.text for element in component if element.tag.endswith(field)), None)
            if value is not None:
                values[field] = value
        components[name] = values
    return components


def _cover(package_name, version):
    return SimpleNamespace(tool_name=f"{package_name} v{version}")


def _get_child(element, suffix):
    return next((child for child in element if child.tag.endswith(suffix)), None)


def _get_bom_components_and_dependencies(result_file, extension):
    if extension == ".json":
        with open(result_file, encoding="utf-8") as cyclonedx_file:
            document = json.load(cyclonedx_file)
        return document["components"], document.get("dependencies", [])

    root = ElementTree.parse(result_file).getroot()
    component_group = _get_child(root, "components")
    components = []
    for component in component_group:
        values = {
            "bom-ref": component.attrib["bom-ref"],
            "name": _get_child(component, "name").text,
            "type": component.attrib["type"],
            "properties": [],
        }
        properties = _get_child(component, "properties")
        if properties is not None:
            values["properties"] = [
                {"name": prop.attrib["name"], "value": prop.text}
                for prop in properties
            ]
        components.append(values)

    dependency_group = _get_child(root, "dependencies")
    dependencies = []
    if dependency_group is not None:
        for dependency in dependency_group:
            dependencies.append({
                "ref": dependency.attrib["ref"],
                "dependsOn": [child.attrib["ref"] for child in dependency],
            })
    return components, dependencies


def _phase_three_scan_item(tmp_path, tlsh="T1VALID"):
    scan_item = ScannerItem(FOSSLIGHT_SCANNER)
    scan_item.set_cover_pathinfo(str(tmp_path / "project"), [])

    source_file = FileItem("LICENSE")
    source_file.source_name_or_path = "LICENSE"
    source_file.oss_items.append(OssItem("", "", "MIT"))
    scan_item.append_file_items([source_file], FOSSLIGHT_SOURCE)

    binary_file = FileItem("app.bin")
    binary_file.source_name_or_path = "app.bin"
    binary_file.checksum = "af969fc2085b1bb6d31e517d5c456def5cdd7093"
    binary_file.tlsh = tlsh
    binary_file.oss_items.append(OssItem("-", "2.0.0", "Apache-2.0"))
    scan_item.append_file_items([binary_file], FOSSLIGHT_BINARY)

    direct_dependency = FileItem("requirements.txt")
    direct_dependency.purl = "pkg:pypi/foo@1.0.0"
    direct_dependency.depends_on = ["pkg:pypi/bar@2.0.0"]
    direct_oss = OssItem("foo", "1.0.0", "MIT")
    direct_oss.comment = "direct"
    direct_dependency.oss_items.append(direct_oss)

    transitive_dependency = FileItem("requirements.txt")
    transitive_dependency.purl = "pkg:pypi/bar@2.0.0"
    transitive_dependency.depends_on = []
    transitive_oss = OssItem("bar", "2.0.0", "BSD-3-Clause")
    transitive_oss.comment = "transitive"
    transitive_dependency.oss_items.append(transitive_oss)

    unnamed_dependency = FileItem("requirements.txt")
    unnamed_dependency.purl = "pkg:pypi/unnamed@3.0.0"
    unnamed_dependency.depends_on = []
    unnamed_oss = OssItem("", "3.0.0", "ISC")
    unnamed_oss.comment = "direct"
    unnamed_dependency.oss_items.append(unnamed_oss)
    scan_item.append_file_items([direct_dependency, transitive_dependency, unnamed_dependency], FOSSLIGHT_DEPENDENCY)

    return scan_item


@pytest.mark.parametrize("extension", [".json", ".xml"])
def test_cyclonedx(scan_item, extension):
    # given
    output_dir = os.path.join(constants.TEST_RESULT_DIR, "cyclonedx")
    output_file_without_ext = os.path.join(output_dir, "FL-TEST_cyclonedx")

    # when
    success, err_msg, result_file = write_cyclonedx(output_file_without_ext, extension, scan_item)

    # then
    assert success is True, err_msg
    assert os.path.isfile(result_file)
    if extension == ".json":
        with open(result_file, encoding="utf-8") as cyclonedx_file:
            document = json.load(cyclonedx_file)
        assert document["bomFormat"] == "CycloneDX"
        assert document["metadata"]["component"] == {
            "bom-ref": "0",
            "name": "test_excel_and_csv",
            "type": "application",
        }
    else:
        root = ElementTree.parse(result_file).getroot()
        assert root.tag.endswith("bom")
        metadata = next(element for element in root if element.tag.endswith("metadata"))
        component = next(element for element in metadata if element.tag.endswith("component"))
        assert component.attrib == {"bom-ref": "0", "type": "application"}
        assert next(element for element in component if element.tag.endswith("name")).text == "test_excel_and_csv"


@pytest.mark.parametrize("extension", [".json", ".xml"])
def test_root_package_does_not_override_metadata_component(tmp_path, extension):
    scan_item = ScannerItem(FOSSLIGHT_DEPENDENCY)
    scan_item.set_cover_pathinfo(str(tmp_path / "example"), [])

    file_item = FileItem("requirements.txt")
    file_item.purl = ""
    file_item.depends_on = []
    root_package = OssItem("root-package", "1.0.0", "MIT")
    root_package.comment = "root package"
    file_item.oss_items.append(root_package)
    scan_item.append_file_items([file_item])

    output_file_without_ext = os.path.join(constants.TEST_RESULT_DIR, "cyclonedx", "root-package")
    success, err_msg, result_file = write_cyclonedx(output_file_without_ext, extension, scan_item)

    assert success is True, err_msg
    if extension == ".json":
        with open(result_file, encoding="utf-8") as cyclonedx_file:
            component = json.load(cyclonedx_file)["metadata"]["component"]
        assert component == {
            "bom-ref": "0",
            "name": "example",
            "type": "application",
        }
    else:
        root = ElementTree.parse(result_file).getroot()
        metadata = next(element for element in root if element.tag.endswith("metadata"))
        component = next(element for element in metadata if element.tag.endswith("component"))
        assert component.attrib == {"bom-ref": "0", "type": "application"}
        assert next(element for element in component if element.tag.endswith("name")).text == "example"


@pytest.mark.parametrize("extension", [".json", ".xml"])
def test_tool_components_use_executed_scanner_covers(tmp_path, extension):
    scan_item = ScannerItem(FOSSLIGHT_DEPENDENCY)
    scan_item.set_cover_pathinfo(str(tmp_path / "example"), [])
    scanner_covers = [
        _cover("fosslight_scanner", "2.1.30"),
        _cover("fosslight_source", "2.3.12"),
        _cover("fosslight_binary", "5.1.32"),
    ]

    output_file_without_ext = os.path.join(constants.TEST_RESULT_DIR, "cyclonedx", "tools")
    success, err_msg, result_file = write_cyclonedx(
        output_file_without_ext, extension, scan_item, scanner_covers=scanner_covers
    )

    assert success is True, err_msg
    components = _get_tool_components(result_file, extension)
    assert components["FOSSLIGHT_SCANNER"]["version"] == "2.1.30"
    assert components["FOSSLIGHT_SCANNER"]["group"] == "FOSSLight"
    assert components["FOSSLIGHT_Source"]["version"] == "2.3.12"
    assert components["FOSSLIGHT_Binary"]["version"] == "5.1.32"
    assert "FOSSLIGHT_Dependency" not in components


def test_tool_components_deduplicate_merged_scanner_cover(tmp_path):
    scan_item = ScannerItem(FOSSLIGHT_DEPENDENCY)
    scan_item.set_cover_pathinfo(str(tmp_path / "example"), [])
    scanner_covers = [
        _cover("fosslight_scanner", "2.1.30 (fosslight_dependency v4.1.51, fosslight_source v2.3.12)"),
        _cover("fosslight_dependency", "4.1.51"),
        _cover("fosslight_dependency", "4.1.51"),
    ]

    output_file_without_ext = os.path.join(constants.TEST_RESULT_DIR, "cyclonedx", "deduplicated-tools")
    success, err_msg, result_file = write_cyclonedx(
        output_file_without_ext, ".json", scan_item, scanner_covers=scanner_covers
    )

    assert success is True, err_msg
    components = _get_tool_components(result_file, ".json")
    assert set(components) == {
        "FOSSLIGHT_SCANNER",
        "FOSSLIGHT_Dependency",
        "cyclonedx-python-lib",
    }
    assert components["FOSSLIGHT_SCANNER"]["version"] == "2.1.30"
    assert components["FOSSLIGHT_Dependency"]["version"] == "4.1.51"


@pytest.mark.parametrize("extension", [".json", ".xml"])
def test_scanner_component_mapping_and_dependency_refs(tmp_path, extension):
    scan_item = _phase_three_scan_item(tmp_path)
    output_file_without_ext = os.path.join(constants.TEST_RESULT_DIR, "cyclonedx", "component-mapping")

    success, err_msg, result_file = write_cyclonedx(output_file_without_ext, extension, scan_item)

    assert success is True, err_msg
    components, dependencies = _get_bom_components_and_dependencies(result_file, extension)
    source_component = next(component for component in components
                            if component["name"] == "NOASSERTION" and component["type"] == "file"
                            and not component.get("properties", []))
    binary_component = next(component for component in components
                            if component["name"] == "NOASSERTION" and component["type"] == "file"
                            and component.get("properties", []))
    dependency_components = [component for component in components if component["name"] in ("foo", "bar")]
    unnamed_dependency_component = next(component for component in components
                                        if component["name"] == "NOASSERTION" and component["type"] == "library")

    assert source_component["type"] == "file"
    assert binary_component["type"] == "file"
    assert len(dependency_components) == 2
    assert all(component["type"] == "library" for component in dependency_components)
    assert unnamed_dependency_component["type"] == "library"
    assert binary_component.get("properties", []) == [{
        "name": "fosslight:tlsh",
        "value": "T1VALID",
    }]

    component_refs = {component["bom-ref"] for component in components} | {"0"}
    assert all(dependency["ref"] in component_refs for dependency in dependencies)
    assert all(ref in component_refs
               for dependency in dependencies for ref in dependency.get("dependsOn", []))
    foo_ref = next(component["bom-ref"] for component in dependency_components if component["name"] == "foo")
    bar_ref = next(component["bom-ref"] for component in dependency_components if component["name"] == "bar")
    assert any(dependency["ref"] == "0" and foo_ref in dependency["dependsOn"] for dependency in dependencies)
    assert any(dependency["ref"] == foo_ref and bar_ref in dependency["dependsOn"] for dependency in dependencies)


@pytest.mark.parametrize("extension", [".json", ".xml"])
@pytest.mark.parametrize("tlsh", ["", "0", "TNULL"])
def test_binary_tlsh_null_markers_are_omitted(tmp_path, extension, tlsh):
    scan_item = _phase_three_scan_item(tmp_path, tlsh=tlsh)
    output_file_without_ext = os.path.join(constants.TEST_RESULT_DIR, "cyclonedx", "tlsh-null")

    success, err_msg, result_file = write_cyclonedx(output_file_without_ext, extension, scan_item)

    assert success is True, err_msg
    components, _ = _get_bom_components_and_dependencies(result_file, extension)
    binary_component = next(component for component in components
                            if component["name"] == "NOASSERTION" and component["type"] == "file")
    assert binary_component.get("properties", []) == []


def test_write_output_file_forwards_scanner_covers(monkeypatch, tmp_path, scan_item):
    scanner_covers = [_cover("fosslight_source", "2.3.12")]
    captured = {}

    def fake_write_cyclonedx(output_file_without_ext, output_extension, item, scanner_covers=None):
        captured["scanner_covers"] = scanner_covers
        return True, "", output_file_without_ext + output_extension

    monkeypatch.setattr("fosslight_util.output_format.write_cyclonedx", fake_write_cyclonedx)
    output_file_without_ext = os.path.join(tmp_path, "tools")

    success, err_msg, result_file = write_output_file(
        output_file_without_ext,
        ".json",
        scan_item,
        format="cyclonedx-json",
        scanner_covers=scanner_covers,
    )

    assert success is True, err_msg
    assert result_file == output_file_without_ext + ".json"
    assert captured["scanner_covers"] == scanner_covers


def test_cyclonedx_import_failure_is_reported(monkeypatch, scan_item):
    monkeypatch.setattr(
        "fosslight_util.write_cyclonedx._cyclonedx_import_error",
        ImportError("cyclonedx is unavailable"),
    )

    success, err_msg, result_file = write_cyclonedx("unused", ".json", scan_item)

    assert success is False
    assert "cyclonedx is unavailable" in err_msg
    assert result_file == ""


def test_cyclonedx_serialization_failure_is_reported(monkeypatch, scan_item):
    output_file_without_ext = os.path.join(constants.TEST_RESULT_DIR, "cyclonedx", "failed")
    monkeypatch.setattr("fosslight_util.write_cyclonedx.write_cyclonedx_json", lambda *_: False)

    success, err_msg, result_file = write_cyclonedx(output_file_without_ext, ".json", scan_item)

    assert success is False
    assert "Failed to write CycloneDX document" in err_msg
    assert not os.path.exists(result_file)


@pytest.mark.parametrize("system", ["Windows", "Darwin"])
def test_cyclonedx_is_supported_on_all_platforms(monkeypatch, scan_item, system):
    monkeypatch.setattr("fosslight_util.output_format.platform.system", lambda: system)
    output_file_without_ext = os.path.join(constants.TEST_RESULT_DIR, system, "cyclonedx")

    success, err_msg, result_file = write_output_file(
        output_file_without_ext, ".json", scan_item, format="cyclonedx-json")

    assert success is True, err_msg
    assert os.path.isfile(result_file)


@pytest.mark.parametrize("system", ["Windows", "Darwin"])
def test_spdx_platform_restriction_is_unchanged(monkeypatch, scan_item, system):
    monkeypatch.setattr("fosslight_util.output_format.platform.system", lambda: system)

    success, err_msg, _ = write_output_file(
        os.path.join(constants.TEST_RESULT_DIR, system, "spdx"),
        ".json",
        scan_item,
        format="spdx-json",
    )

    assert success is False
    assert err_msg == f"{system} not support spdx format."
