# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for link-version then checkout-version download attempts."""

import logging

import pytest

from fosslight_util import _get_downloadable_url as downloadable_url
from fosslight_util import download as download_module


GO_LINK = (
    "https://pkg.go.dev/github.com/DataDog/datadog-agent/"
    "comp/core/tagger/origindetection/@0.77.0"
)
GO_BARE = (
    "https://pkg.go.dev/github.com/DataDog/datadog-agent/"
    "comp/core/tagger/origindetection"
)
GO_MODULE = (
    "github.com/DataDog/datadog-agent/comp/core/tagger/origindetection"
)


class _FakeResponse:
    def __init__(self, status_code=200, text="", payload=None):
        self.status_code = status_code
        self.text = text
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


def test_go_proxy_escape_encodes_uppercase():
    assert downloadable_url._go_proxy_escape(GO_MODULE) == (
        "github.com/!data!dog/datadog-agent/comp/core/tagger/origindetection"
    )


def test_split_pkg_link_version_reads_slash_at_version():
    bare, version = downloadable_url.split_pkg_link_version(GO_LINK)
    assert bare == GO_BARE
    assert version == "0.77.0"


def test_split_pkg_link_version_reads_at_v_version():
    bare, version = downloadable_url.split_pkg_link_version(
        "https://pkg.go.dev/github.com/go-openapi/jsonreference@v0.20.2"
    )
    assert bare == "https://pkg.go.dev/github.com/go-openapi/jsonreference"
    assert version == "0.20.2"


def test_split_pkg_link_version_keeps_url_without_version():
    bare, version = downloadable_url.split_pkg_link_version(GO_BARE)
    assert bare == GO_BARE
    assert version == ""


def test_download_version_attempts_tries_link_then_checkout():
    attempts = downloadable_url.download_version_attempts(GO_LINK, "0.77.0")
    assert attempts == [
        (GO_LINK, "", False),
        (GO_BARE, "0.77.0", True),
    ]


def test_download_version_attempts_single_try_without_embedded_version():
    attempts = downloadable_url.download_version_attempts(
        "https://github.com/foo/bar", "1.2.3"
    )
    assert attempts == [("https://github.com/foo/bar", "1.2.3", True)]


def test_go_version_exists_uses_proxy_case_encoding(monkeypatch):
    seen = {}

    def fake_get(url, timeout=5):
        seen["url"] = url
        return _FakeResponse(200, text="v0.76.0\nv0.77.0\n")

    monkeypatch.setattr(downloadable_url.requests, "get", fake_get)
    assert downloadable_url.version_exists("go", GO_MODULE, "0.77.0") is True
    assert "!data!dog" in seen["url"]
    assert seen["url"].endswith("/@v/list")


def test_go_zip_url_case_encodes_module(monkeypatch):
    seen = {}

    class _Response:
        def getcode(self):
            return 200

    def fake_urlopen(url, timeout=None):
        seen["url"] = url
        return _Response()

    monkeypatch.setattr(downloadable_url, "urlopen", fake_urlopen)
    ok, link = downloadable_url.get_download_location_for_go(
        "https://pkg.go.dev/" + GO_MODULE + "@v0.77.0"
    )
    assert ok is True
    assert link == (
        "https://proxy.golang.org/github.com/!data!dog/datadog-agent/"
        "comp/core/tagger/origindetection/@v/v0.77.0.zip"
    )
    assert seen["url"] == link


def test_missing_link_version_is_not_replaced_when_latest_is_disabled(monkeypatch):
    monkeypatch.setattr(downloadable_url, "version_exists", lambda *args, **kwargs: False)

    def fail_latest(*args, **kwargs):
        raise AssertionError("latest version must not be queried")

    monkeypatch.setattr(downloadable_url, "get_latest_package_version", fail_latest)
    _name, version, link, pkg_type = downloadable_url.extract_name_version_from_link(
        GO_LINK, "", allow_latest=False
    )
    assert pkg_type == "go"
    assert version == "0.77.0"
    assert link.endswith("@v0.77.0")
    assert "DataDog" in link


def test_missing_checkout_version_falls_back_to_latest(monkeypatch):
    monkeypatch.setattr(downloadable_url, "version_exists", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        downloadable_url,
        "get_latest_package_version",
        lambda *args, **kwargs: "9.9.9",
    )
    _name, version, link, _pkg = downloadable_url.extract_name_version_from_link(
        GO_BARE, "0.1.0", allow_latest=True
    )
    assert version == "9.9.9"
    assert link.endswith("@v9.9.9")


def test_cli_retries_checkout_after_link_version_fails(tmp_path, monkeypatch):
    calls = []

    def fake_git(git_url, target_dir, checkout_to="", *args, **kwargs):
        calls.append(("git", git_url, checkout_to))
        return False, "git failed", "", "", ""

    def fake_wget(link, target_dir, compressed_only, checkout_to, size_limit_gb=None,
                  allow_latest=True):
        calls.append(("wget", link, checkout_to, allow_latest))
        if not allow_latest:
            return False, "", "Not a downloadable link", "", "", ""
        return True, str(tmp_path / "mod.zip"), "", "go:" + GO_MODULE, "0.77.0", link

    monkeypatch.setattr(download_module, "download_git_clone", fake_git)
    monkeypatch.setattr(download_module, "download_wget", fake_wget)
    monkeypatch.setattr(download_module, "extract_compressed_file", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        download_module,
        "init_log",
        lambda *args, **kwargs: (logging.getLogger("fosslight_download_test"), None),
    )

    success, msg, oss_name, oss_version, _clarified = download_module.cli_download_and_extract(
        GO_LINK,
        str(tmp_path / "out"),
        str(tmp_path / "log"),
        checkout_to="0.77.0",
        called_cli=False,
    )

    assert success is True
    assert msg == ""
    assert oss_version == "0.77.0"
    assert oss_name == "go:" + GO_MODULE
    assert calls == [
        ("git", GO_LINK, ""),
        ("wget", GO_LINK, "", False),
        ("git", GO_BARE, "0.77.0"),
        ("wget", GO_BARE, "0.77.0", True),
    ]


def test_cli_does_not_retry_after_size_limit(tmp_path, monkeypatch):
    calls = []

    def fake_git(git_url, target_dir, checkout_to="", *args, **kwargs):
        calls.append(checkout_to)
        return False, "Download aborted due to size limit", "", "", ""

    def fake_wget(*args, **kwargs):
        raise AssertionError("wget must not run after a size-limit failure")

    monkeypatch.setattr(download_module, "download_git_clone", fake_git)
    monkeypatch.setattr(download_module, "download_wget", fake_wget)
    monkeypatch.setattr(
        download_module,
        "init_log",
        lambda *args, **kwargs: (logging.getLogger("fosslight_download_test"), None),
    )

    success, msg, *_rest = download_module.cli_download_and_extract(
        GO_LINK,
        str(tmp_path / "out"),
        str(tmp_path / "log"),
        checkout_to="0.77.0",
        called_cli=False,
    )

    assert success is False
    assert "size limit" in msg
    assert calls == [""]


@pytest.mark.parametrize("checkout_to", ["", "   "])
def test_download_version_attempts_without_checkout_is_one_try(checkout_to):
    attempts = downloadable_url.download_version_attempts(GO_LINK, checkout_to)
    assert attempts == [(GO_LINK, checkout_to, True)]
