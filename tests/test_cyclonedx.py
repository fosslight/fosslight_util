# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import json
import os
import xml.etree.ElementTree as ElementTree

import pytest

from fosslight_util.output_format import write_output_file
from fosslight_util.constant import FOSSLIGHT_DEPENDENCY
from fosslight_util.oss_item import FileItem, OssItem, ScannerItem
from fosslight_util.write_cyclonedx import write_cyclonedx
from tests import constants


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
