# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for Packagist (PHP/Composer) download URL resolution."""

import os

import pytest

from fosslight_util import _get_downloadable_url as downloadable_url
from fosslight_util.download import cli_download_and_extract
from tests import constants


_MUSTACHE_PACKAGES = [
    {
        "version": "v3.2.0",
        "version_normalized": "3.2.0.0",
        "dist": {
            "url": "https://api.github.com/repos/bobthecow/mustache.php/zipball/abc123",
            "type": "zip",
            "reference": "abc123",
        },
        "source": {
            "url": "https://github.com/bobthecow/mustache.php.git",
            "type": "git",
            "reference": "abc123",
        },
    },
    {
        "version": "v2.14.2",
        "version_normalized": "2.14.2.0",
        "dist": {
            "url": "https://api.github.com/repos/bobthecow/mustache.php/zipball/def456",
            "type": "zip",
            "reference": "def456",
        },
        "source": {
            "url": "https://github.com/bobthecow/mustache.php.git",
            "type": "git",
            "reference": "def456",
        },
    },
]


class _FakeJsonResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


def test_packagist_pattern_extracts_name_and_fragment_version(monkeypatch):
    monkeypatch.setattr(
        downloadable_url, "_fetch_packagist_packages", lambda _: _MUSTACHE_PACKAGES
    )
    name, version, link, pkg_type = downloadable_url.extract_name_version_from_link(
        "https://packagist.org/packages/mustache/mustache#v2.14.2",
        "",
    )
    assert pkg_type == "packagist"
    assert name == "packagist:mustache/mustache"
    assert version in ("2.14.2", "v2.14.2")
    assert "mustache/mustache" in link


def test_find_packagist_package_entry_matches_with_or_without_v():
    pkg = downloadable_url._find_packagist_package_entry(_MUSTACHE_PACKAGES, "2.14.2")
    assert pkg is not None
    assert pkg["version"] == "v2.14.2"

    pkg = downloadable_url._find_packagist_package_entry(_MUSTACHE_PACKAGES, "v2.14.2")
    assert pkg is not None
    assert pkg["version"] == "v2.14.2"

    latest = downloadable_url._find_packagist_package_entry(_MUSTACHE_PACKAGES, "")
    assert latest["version"] == "v3.2.0"


def test_archive_url_from_packagist_source_github():
    url = downloadable_url._archive_url_from_packagist_source(
        {
            "type": "git",
            "url": "https://github.com/bobthecow/mustache.php.git",
            "reference": "deadbeef",
        }
    )
    assert url == "https://github.com/bobthecow/mustache.php/archive/deadbeef.zip"


def test_get_download_location_for_packagist_uses_dist_url(monkeypatch):
    def fake_fetch(package_name):
        assert package_name == "mustache/mustache"
        return _MUSTACHE_PACKAGES

    monkeypatch.setattr(downloadable_url, "_fetch_packagist_packages", fake_fetch)

    ok, link = downloadable_url.get_download_location_for_packagist(
        "packagist.org/packages/mustache/mustache/v2.14.2"
    )
    assert ok is True
    assert link == "https://api.github.com/repos/bobthecow/mustache.php/zipball/def456"


def test_get_download_location_for_packagist_falls_back_to_source_archive(monkeypatch):
    packages = [
        {
            "version": "v1.0.0",
            "version_normalized": "1.0.0.0",
            "dist": {},
            "source": {
                "type": "git",
                "url": "https://github.com/acme/demo.git",
                "reference": "111aaa",
            },
        }
    ]
    monkeypatch.setattr(downloadable_url, "_fetch_packagist_packages", lambda _: packages)

    ok, link = downloadable_url.get_download_location_for_packagist(
        "packagist.org/packages/acme/demo/v1.0.0"
    )
    assert ok is True
    assert link == "https://github.com/acme/demo/archive/111aaa.zip"


def test_get_downloadable_url_packagist_latest(monkeypatch):
    monkeypatch.setattr(
        downloadable_url, "_fetch_packagist_packages", lambda _: _MUSTACHE_PACKAGES
    )

    ok, link, oss_name, oss_version, pkg_type = downloadable_url.get_downloadable_url(
        "https://packagist.org/packages/mustache/mustache",
        "",
    )
    assert ok is True
    assert pkg_type == "packagist"
    assert oss_name == "packagist:mustache/mustache"
    assert oss_version == "v3.2.0"
    assert link.endswith("/zipball/abc123")


def test_get_downloadable_url_packagist_checkout_version(monkeypatch):
    monkeypatch.setattr(
        downloadable_url, "_fetch_packagist_packages", lambda _: _MUSTACHE_PACKAGES
    )

    ok, link, oss_name, oss_version, pkg_type = downloadable_url.get_downloadable_url(
        "https://packagist.org/packages/mustache/mustache",
        "v2.14.2",
    )
    assert ok is True
    assert pkg_type == "packagist"
    assert oss_name == "packagist:mustache/mustache"
    assert oss_version == "v2.14.2"
    assert link.endswith("/zipball/def456")


@pytest.mark.parametrize(
    "project_url",
    [
        "https://packagist.org/packages/mustache/mustache",
        "https://packagist.org/packages/mustache/mustache#v2.14.2",
    ],
)
def test_download_packagist_live(project_url):
    target_dir = os.path.join(constants.TEST_RESULT_DIR, "download/packagist_mustache")
    log_dir = os.path.join(constants.TEST_RESULT_DIR, "download_log/packagist_mustache")

    success, _, _, _, _ = cli_download_and_extract(project_url, target_dir, log_dir)

    assert success is True
    assert len(os.listdir(target_dir)) > 0
