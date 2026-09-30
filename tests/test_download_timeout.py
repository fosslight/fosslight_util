# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the overall download timeout (the watchdog), not the no-response timeouts."""

import io
import os
import subprocess
import sys
import tarfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import fosslight_util.download as download
from fosslight_util.download import cli_download_and_extract

_BLOCK = 8192
_BLOCK_INTERVAL_SEC = 0.4


def _make_tar_gz() -> bytes:
    # Random content does not compress, so the archive spans several blocks.
    payload = os.urandom(_BLOCK * 5)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo("pkg/data.bin")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    return buf.getvalue()


@pytest.fixture
def slow_archive_url():
    """Serve a valid .tar.gz slowly: healthy, just slower than a short timeout."""
    body = _make_tar_gz()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/pkg.tar.gz":
                # Makes the git clone attempt that runs first fail fast.
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                for i in range(0, len(body), _BLOCK):
                    self.wfile.write(body[i:i + _BLOCK])
                    self.wfile.flush()
                    time.sleep(_BLOCK_INTERVAL_SEC)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

        def do_HEAD(self):
            self.send_error(404)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/pkg.tar.gz", len(body)
    finally:
        server.shutdown()


@pytest.fixture
def no_system_wget(monkeypatch):
    """Fail the test if the download is started over with system wget."""
    def fail(*args, **kwargs):
        raise AssertionError("system wget must not be tried after a timeout")
    monkeypatch.setattr(download, "_download_with_system_wget", fail)


def test_timeout_zero_or_negative_turns_the_watchdog_off():
    assert download._start_download_watchdog(0) is None
    assert download._start_download_watchdog(-1) is None


def test_default_timeout_is_signal_timeout():
    alarm = download._start_download_watchdog()
    try:
        assert alarm.timeout == download.SIGNAL_TIMEOUT == 600
    finally:
        download._cancel_download_watchdog(alarm)


def test_timeout_stops_download_and_returns_failure(tmp_path, slow_archive_url, no_system_wget):
    # given: the archive needs about 2 seconds, the timeout is 1 second
    url, total_size = slow_archive_url
    target = tmp_path / "target"

    # when
    started = time.monotonic()
    success, msg, *_ = cli_download_and_extract(url, str(target), str(tmp_path), timeout=1)
    elapsed = time.monotonic() - started

    # then: a failure result, not a process exit
    assert success is False
    assert msg == "Download timeout 1s"
    assert elapsed < 10, f"the download should stop soon after the timeout, took {elapsed:.1f}s"
    # the partial download is left for the user to handle
    partial = target / "pkg.tar.gz"
    assert partial.is_file(), f"partial download should be kept: {list(target.iterdir())}"
    assert 0 < partial.stat().st_size < total_size


def test_timeout_off_lets_a_slow_download_finish(tmp_path, slow_archive_url, no_system_wget):
    # given: the same slow archive, with the overall timeout turned off
    url, _ = slow_archive_url
    target = tmp_path / "target"

    # when
    success, msg, *_ = cli_download_and_extract(url, str(target), str(tmp_path), timeout=0)

    # then: downloaded and extracted
    assert success is True, msg
    assert (target / "pkg" / "data.bin").is_file()


def test_timeout_stops_system_wget(tmp_path, monkeypatch):
    # given: a "wget" that would run for a minute, and a watchdog that fires after 1 second
    started = []
    real_popen = subprocess.Popen

    def fake_popen(args, **kwargs):
        proc = real_popen([sys.executable, "-c", "import time; time.sleep(60)"], **kwargs)
        started.append(proc)
        return proc

    def offline(*args, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr(download.shutil, "which", lambda name: "wget")
    monkeypatch.setattr(download.requests, "head", offline)
    monkeypatch.setattr(download.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(download, "SIZE_CHECK_INTERVAL_SECONDS", 0.1)
    alarm = download._start_download_watchdog(1)

    # when / then
    try:
        with pytest.raises(download.TimeOutException, match="Download timeout 1s"):
            download._download_with_system_wget("http://127.0.0.1:9/pkg.tar.gz", str(tmp_path))
    finally:
        download._cancel_download_watchdog(alarm)

    assert started and started[0].poll() is not None, "wget should have been stopped"
