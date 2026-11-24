# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""PyPI project URLs resolve to the file URL from the JSON API."""

from unittest.mock import Mock, patch

from fosslight_util._get_downloadable_url import get_download_location_for_pypi

_SDIST = (
    "https://files.pythonhosted.org/packages/9b/5a/abc/"
    "winrt_windows_storage_streams-4!10.0.28000.2957.tar.gz"
)
_WHEEL = (
    "https://files.pythonhosted.org/packages/d5/8d/abc/"
    "winrt_windows_storage_streams-4!10.0.28000.2957-py3-none-any.whl"
)
_PROJECT = "https://pypi.org/project/winrt-Windows.Storage.Streams/4!10.0.28000.2957"


def _response(status_code, urls):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = {"urls": urls}
    return response


@patch("fosslight_util._get_downloadable_url.requests.get")
def test_pypi_json_prefers_sdist_for_mixed_case_name(mock_get):
    mock_get.return_value = _response(200, [
        {"packagetype": "bdist_wheel", "filename": "pkg.whl", "url": _WHEEL},
        {"packagetype": "sdist", "filename": "pkg.tar.gz", "url": _SDIST},
        {"packagetype": "sdist", "filename": "pkg.zip", "url": "https://example.invalid/pkg.zip"},
    ])

    found, link = get_download_location_for_pypi(_PROJECT)

    assert found is True
    assert link == _SDIST
    requested = mock_get.call_args.args[0]
    assert "winrt-Windows.Storage.Streams" in requested
    assert "4%2110.0.28000.2957" in requested
    assert "packages/source/" not in link


@patch("fosslight_util._get_downloadable_url.requests.get")
def test_pypi_json_uses_pure_wheel_when_sdist_is_missing(mock_get):
    platform_wheel = "https://files.pythonhosted.org/packages/aa/pkg-1.0-cp312-cp312-win_amd64.whl"
    mock_get.return_value = _response(200, [
        {"packagetype": "bdist_wheel", "filename": "pkg.whl", "url": platform_wheel},
        {"packagetype": "bdist_wheel", "filename": "pkg-none.whl", "url": _WHEEL},
    ])

    found, link = get_download_location_for_pypi("https://pypi.org/project/pkg/1.0")

    assert found is True
    assert link == _WHEEL


@patch("fosslight_util._get_downloadable_url.requests.get")
def test_pypi_json_keeps_yanked_release_file(mock_get):
    mock_get.return_value = _response(200, [
        {"packagetype": "bdist_wheel", "filename": "pkg.whl", "url": _WHEEL, "yanked": True},
        {"packagetype": "sdist", "filename": "pkg.tar.gz", "url": _SDIST, "yanked": True},
    ])

    found, link = get_download_location_for_pypi(_PROJECT)

    assert found is True
    assert link == _SDIST


@patch("fosslight_util._get_downloadable_url.requests.get")
def test_pypi_json_decodes_percent_encoded_version(mock_get):
    mock_get.return_value = _response(200, [
        {"packagetype": "sdist", "filename": "pkg.tar.gz", "url": _SDIST},
    ])
    encoded = "https://pypi.org/project/winrt-Windows.Storage.Streams/4%2110.0.28000.2957"

    found, link = get_download_location_for_pypi(encoded)

    assert found is True
    assert link == _SDIST
    encoded_request = mock_get.call_args.args[0]
    assert "4%2110.0.28000.2957" in encoded_request
    assert "%2521" not in encoded_request

    mock_get.reset_mock()
    mock_get.return_value = _response(200, [
        {"packagetype": "sdist", "filename": "pkg.tar.gz", "url": _SDIST},
    ])
    get_download_location_for_pypi(_PROJECT)
    assert mock_get.call_args.args[0] == encoded_request


@patch("fosslight_util._get_downloadable_url.requests.get")
def test_pypi_json_failure_does_not_invent_a_file_url(mock_get):
    mock_get.return_value = _response(404, [])

    found, link = get_download_location_for_pypi(_PROJECT)

    assert found is False
    assert link == ""
