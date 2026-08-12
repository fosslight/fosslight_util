# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for Maven repository probing and exact-version preference."""

import pytest

from fosslight_util import _get_downloadable_url as downloadable_url


class _FakeResponse:
    def __init__(self, status_code=200, payload=None, text="", content=b""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text
        self.content = content

    def json(self):
        return self._payload

    def close(self):
        return None


def test_version_exists_keeps_non_central_maven_version(monkeypatch):
    """Central index miss must not reject a version hosted on another known repo."""

    def fake_get(url, timeout=5):
        assert "deps.dev" in url
        return _FakeResponse(200, {"versions": [{"versionKey": {"version": "6.1.14"}}]})

    monkeypatch.setattr(downloadable_url.requests, "get", fake_get)
    monkeypatch.setattr(
        downloadable_url,
        "_maven_version_available",
        lambda group_path, artifact_id, version: (
            group_path == "org/springframework"
            and artifact_id == "spring-core"
            and version == "6.2.0-M1"
        ),
    )

    assert downloadable_url.version_exists(
        "maven", "org.springframework:spring-core", "6.2.0-M1"
    ) is True
    assert downloadable_url.version_exists(
        "maven", "org.springframework:spring-core", "9.9.9"
    ) is False


def test_extract_keeps_exact_version_when_found_on_candidate_repo(monkeypatch):
    monkeypatch.setattr(
        downloadable_url,
        "version_exists",
        lambda pkg_type, origin_name, version: version == "6.2.0-M1",
    )
    monkeypatch.setattr(
        downloadable_url,
        "get_latest_package_version",
        lambda *_args, **_kwargs: pytest.fail("latest fallback must not run"),
    )

    name, version, link, pkg_type = downloadable_url.extract_name_version_from_link(
        "https://mvnrepository.com/artifact/org.springframework/spring-core/6.2.0-M1",
        "",
    )
    assert pkg_type == "maven"
    assert name == "org.springframework:spring-core"
    assert version == "6.2.0-M1"
    assert link.endswith("/spring-core/6.2.0-M1")


def test_extract_falls_back_to_latest_only_when_no_repo_has_version(monkeypatch):
    monkeypatch.setattr(
        downloadable_url,
        "version_exists",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        downloadable_url,
        "get_latest_package_version",
        lambda *_args, **_kwargs: "6.1.14",
    )

    name, version, link, pkg_type = downloadable_url.extract_name_version_from_link(
        "https://mvnrepository.com/artifact/org.springframework/spring-core/9.9.9-NOT-EXIST",
        "",
    )
    assert pkg_type == "maven"
    assert name == "org.springframework:spring-core"
    assert version == "6.1.14"
    assert link.endswith("/spring-core/6.1.14")


def test_probe_maven_sources_prefers_repo_with_exact_version(monkeypatch):
    central = "https://repo1.maven.org/maven2"
    spring_milestone = "https://repo.spring.io/milestone"
    monkeypatch.setattr(
        downloadable_url,
        "MAVEN_REPOSITORY_BASES",
        (central, spring_milestone),
    )
    downloadable_url._MAVEN_SOURCES_PROBE_CACHE.clear()

    def fake_http_ok(url, timeout=None):
        return (
            url
            == f"{spring_milestone}/org/springframework/spring-core/6.2.0-M1/"
            "spring-core-6.2.0-M1-sources.jar"
        )

    monkeypatch.setattr(downloadable_url, "_maven_http_ok", fake_http_ok)
    monkeypatch.setattr(
        downloadable_url,
        "_maven_sources_from_directory",
        lambda *_args, **_kwargs: "",
    )

    found = downloadable_url._probe_maven_sources_jar(
        "org/springframework", "spring-core", "6.2.0-M1"
    )
    assert found == (
        f"{spring_milestone}/org/springframework/spring-core/6.2.0-M1/"
        "spring-core-6.2.0-M1-sources.jar"
    )


def test_maven_repo_bases_for_prefers_group_hints():
    bases = downloadable_url._maven_repo_bases_for("io/confluent")
    assert bases[0] == "https://packages.confluent.io/maven"
    assert "https://repo1.maven.org/maven2" in bases

    spring_bases = downloadable_url._maven_repo_bases_for("org/springframework")
    assert spring_bases[0] == "https://repo.spring.io/milestone"


def test_probe_maven_sources_reuses_cache(monkeypatch):
    downloadable_url._MAVEN_SOURCES_PROBE_CACHE.clear()
    calls = {"n": 0}

    def fake_http_ok(url, timeout=None):
        calls["n"] += 1
        return url.endswith("common-utils-8.2.1-sources.jar") and "packages.confluent.io" in url

    monkeypatch.setattr(downloadable_url, "_maven_http_ok", fake_http_ok)
    monkeypatch.setattr(
        downloadable_url,
        "_maven_sources_from_directory",
        lambda *_args, **_kwargs: "",
    )
    monkeypatch.setattr(
        downloadable_url,
        "MAVEN_REPOSITORY_BASES",
        (
            "https://repo1.maven.org/maven2",
            "https://packages.confluent.io/maven",
        ),
    )

    first = downloadable_url._probe_maven_sources_jar(
        "io/confluent", "common-utils", "8.2.1"
    )
    second = downloadable_url._probe_maven_sources_jar(
        "io/confluent", "common-utils", "8.2.1"
    )
    assert first == second
    assert first.endswith("common-utils-8.2.1-sources.jar")
    assert calls["n"] == 1  # second call served from cache


def test_get_download_location_for_maven_uses_candidate_sources(monkeypatch):
    expected = (
        "https://packages.confluent.io/maven/io/confluent/"
        "kafka-avro-serializer/8.2.1/kafka-avro-serializer-8.2.1-sources.jar"
    )
    monkeypatch.setattr(
        downloadable_url,
        "_probe_maven_sources_jar",
        lambda group_path, artifact_id, version: expected
        if (group_path, artifact_id, version)
        == ("io/confluent", "kafka-avro-serializer", "8.2.1")
        else "",
    )

    ok, url = downloadable_url.get_download_location_for_maven(
        "mvnrepository.com/artifact/io.confluent/kafka-avro-serializer/8.2.1"
    )
    assert ok is True
    assert url == expected


def test_get_latest_package_version_uses_highest_priority_repo_metadata(monkeypatch):
    central = "https://repo1.maven.org/maven2"
    spring = "https://repo.spring.io/milestone"
    monkeypatch.setattr(
        downloadable_url,
        "_maven_repo_bases_for",
        lambda group_path: (central, spring),
    )

    def fake_latest(repo_base, group_path, artifact_id):
        assert group_path == "org/springframework"
        assert artifact_id == "spring-core"
        if repo_base == central:
            return "6.1.14"
        if repo_base == spring:
            return "6.2.0-M1"
        return ""

    monkeypatch.setattr(downloadable_url, "_maven_latest_version_from_repo", fake_latest)
    # deps.dev must not be consulted when a high-priority repo already answered.
    monkeypatch.setattr(
        downloadable_url.requests,
        "get",
        lambda *_args, **_kwargs: pytest.fail("deps.dev fallback must not run"),
    )

    latest = downloadable_url.get_latest_package_version(
        "https://mvnrepository.com/artifact/org.springframework/spring-core",
        "maven",
        "org.springframework:spring-core",
    )
    assert latest == "6.1.14"


def test_maven_latest_version_from_repo_parses_metadata(monkeypatch):
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <metadata>
      <versioning>
        <latest>6.2.0-M3</latest>
        <release>6.1.14</release>
        <versions>
          <version>6.1.13</version>
          <version>6.1.14</version>
          <version>6.2.0-M3</version>
        </versions>
      </versioning>
    </metadata>
    """

    monkeypatch.setattr(
        downloadable_url.requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse(200, content=xml),
    )
    assert (
        downloadable_url._maven_latest_version_from_repo(
            "https://repo1.maven.org/maven2",
            "org/springframework",
            "spring-core",
        )
        == "6.1.14"
    )
