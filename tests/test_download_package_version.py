# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Package-manager version lookup tries a leading v before the latest release."""

import pytest

from fosslight_util import _get_downloadable_url as downloadable_url


def test_go_link_keeps_v_prefix_in_version(monkeypatch):
    seen = []

    def fake_exists(_pkg_type, _origin_name, version):
        seen.append(version)
        return version == "v0.20.2"

    monkeypatch.setattr(downloadable_url, "version_exists", fake_exists)
    monkeypatch.setattr(
        downloadable_url,
        "get_latest_package_version",
        lambda *_args, **_kwargs: pytest.fail("latest fallback must not run"),
    )

    name, version, link, pkg_type = downloadable_url.extract_name_version_from_link(
        "https://pkg.go.dev/github.com/go-openapi/jsonreference@v0.20.2",
        "",
    )

    assert pkg_type == "go"
    assert name == "go:github.com/go-openapi/jsonreference"
    assert seen == ["v0.20.2"]
    assert version == "v0.20.2"
    assert link == "https://pkg.go.dev/github.com/go-openapi/jsonreference@v0.20.2"


def test_go_version_without_v_is_retried_with_v_prefix(monkeypatch):
    seen = []

    def fake_exists(_pkg_type, _origin_name, version):
        seen.append(version)
        return version == "v0.20.2"

    monkeypatch.setattr(downloadable_url, "version_exists", fake_exists)
    monkeypatch.setattr(
        downloadable_url,
        "get_latest_package_version",
        lambda *_args, **_kwargs: pytest.fail("latest fallback must not run"),
    )

    name, version, link, pkg_type = downloadable_url.extract_name_version_from_link(
        "https://pkg.go.dev/github.com/go-openapi/jsonreference@0.20.2",
        "",
    )

    assert pkg_type == "go"
    assert name == "go:github.com/go-openapi/jsonreference"
    assert seen == ["0.20.2", "v0.20.2"]
    assert version == "v0.20.2"
    assert link.endswith("@v0.20.2")


def test_unprefixed_checkout_version_uses_v_prefix_when_present(monkeypatch):
    seen = []

    def fake_exists(_pkg_type, _origin_name, version):
        seen.append(version)
        return version == "v0.20.2"

    monkeypatch.setattr(downloadable_url, "version_exists", fake_exists)

    _name, version, link, pkg_type = downloadable_url.extract_name_version_from_link(
        "https://pkg.go.dev/github.com/go-openapi/jsonreference",
        "0.20.2",
    )

    assert pkg_type == "go"
    assert seen == ["0.20.2", "v0.20.2"]
    assert version == "v0.20.2"
    assert link.endswith("@v0.20.2")


def test_missing_v_and_plain_version_falls_back_to_latest(monkeypatch):
    monkeypatch.setattr(downloadable_url, "version_exists", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(downloadable_url, "get_latest_package_version", lambda *_args, **_kwargs: "v0.21.0")

    _name, version, link, _pkg_type = downloadable_url.extract_name_version_from_link(
        "https://pkg.go.dev/github.com/go-openapi/jsonreference@0.0.1",
        "",
    )

    assert version == "v0.21.0"
    assert link.endswith("@v0.21.0")


def test_leading_v_still_falls_back_to_version_without_v(monkeypatch):
    def fake_exists(_pkg_type, _origin_name, version):
        return version == "1.2.3"

    monkeypatch.setattr(downloadable_url, "version_exists", fake_exists)

    _name, version, link, pkg_type = downloadable_url.extract_name_version_from_link(
        "https://pypi.org/project/example/v1.2.3",
        "",
    )

    assert pkg_type == "pypi"
    assert version == "1.2.3"
    assert link.endswith("/example/1.2.3")


def test_go_download_url_adds_missing_v_prefix(monkeypatch):
    requested = []

    class _Response:
        def getcode(self):
            return 200

    def fake_urlopen(url, timeout=0):
        requested.append(url)
        return _Response()

    monkeypatch.setattr(downloadable_url, "urlopen", fake_urlopen)

    found, new_link = downloadable_url.get_download_location_for_go(
        "pkg.go.dev/github.com/go-openapi/jsonreference@0.20.2"
    )

    assert found is True
    assert requested == [
        "https://proxy.golang.org/github.com/go-openapi/jsonreference/@v/v0.20.2.zip"
    ]
    assert new_link == requested[0]
