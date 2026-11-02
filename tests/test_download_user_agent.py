# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""User-Agent retry when a host blocks non-browser clients with HTTP 400."""

import requests

import fosslight_util.download as download

_JAR_URL = (
    "https://maven.egovframe.go.kr/maven/org/egovframe/rte/"
    "org.egovframe.rte.fdl.cmmn/4.1.0/org.egovframe.rte.fdl.cmmn-4.1.0.jar"
)


class _Response:
    def __init__(self, status_code, body=b"PK\x03\x04", headers=None):
        self.status_code = status_code
        self._body = body
        self.headers = headers or {"content-type": "application/java-archive"}
        self.url = _JAR_URL

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def iter_content(self, chunk_size=8192):
        yield self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _user_agent(kwargs):
    headers = kwargs.get("headers") or {}
    return headers.get("User-Agent")


def test_download_file_retries_http_400_with_browser_user_agent(tmp_path, monkeypatch):
    seen = []

    def fake_head(url, **kwargs):
        seen.append(("head", _user_agent(kwargs)))
        status = 400 if _user_agent(kwargs) == download._HTTP_CURL_LIKE_USER_AGENT else 200
        return _Response(status)

    def fake_get(url, **kwargs):
        seen.append(("get", _user_agent(kwargs)))
        status = 400 if _user_agent(kwargs) == download._HTTP_CURL_LIKE_USER_AGENT else 200
        return _Response(status, body=b"PK\x03\x04jar")

    monkeypatch.setattr(download.requests, "head", fake_head)
    monkeypatch.setattr(download.requests, "get", fake_get)

    path = download.download_file(_JAR_URL, str(tmp_path))

    assert path is not None
    with open(path, "rb") as downloaded:
        assert downloaded.read() == b"PK\x03\x04jar"
    assert seen == [
        ("head", download._HTTP_CURL_LIKE_USER_AGENT),
        ("get", download._HTTP_CURL_LIKE_USER_AGENT),
        ("head", download._HTTP_BROWSER_USER_AGENT),
        ("get", download._HTTP_BROWSER_USER_AGENT),
    ]


def test_download_file_does_not_retry_http_404(tmp_path, monkeypatch):
    seen = []

    def fake_head(url, **kwargs):
        seen.append("head")
        return _Response(404)

    def fake_get(url, **kwargs):
        seen.append("get")
        return _Response(404)

    monkeypatch.setattr(download.requests, "head", fake_head)
    monkeypatch.setattr(download.requests, "get", fake_get)

    assert download.download_file(_JAR_URL, str(tmp_path)) is None
    assert seen == ["head", "get"]


def test_is_downloadable_retries_http_400(monkeypatch):
    seen = []

    def fake_get(url, **kwargs):
        ua = _user_agent(kwargs)
        seen.append(ua)
        status = 400 if ua == download._HTTP_CURL_LIKE_USER_AGENT else 200
        return _Response(status)

    monkeypatch.setattr(download.requests, "get", fake_get)

    assert download.is_downloadable(_JAR_URL) is True
    assert seen == [
        download._HTTP_CURL_LIKE_USER_AGENT,
        download._HTTP_BROWSER_USER_AGENT,
    ]


def test_system_wget_sends_browser_user_agent(tmp_path, monkeypatch):
    captured = {}

    class _Proc:
        returncode = 0

        def poll(self):
            return 0

        def communicate(self):
            return ("", "")

    def fake_popen(cmd, **kwargs):
        captured["cmd"] = cmd
        (tmp_path / "org.egovframe.rte.fdl.cmmn-4.1.0.jar").write_bytes(b"PK")
        return _Proc()

    class _Head:
        status_code = 200
        headers = {}

    def fake_head(url, **kwargs):
        captured["head_headers"] = kwargs.get("headers")
        return _Head()

    monkeypatch.setattr(download.shutil, "which", lambda name: "/usr/bin/wget")
    monkeypatch.setattr(download.requests, "head", fake_head)
    monkeypatch.setattr(download.subprocess, "Popen", fake_popen)

    path = download._download_with_system_wget(_JAR_URL, str(tmp_path))

    assert path.endswith("org.egovframe.rte.fdl.cmmn-4.1.0.jar")
    cmd = captured["cmd"]
    agent_index = cmd.index("--user-agent")
    assert cmd[agent_index + 1] == download._HTTP_BROWSER_USER_AGENT
    assert captured["head_headers"]["User-Agent"] == download._HTTP_BROWSER_USER_AGENT
