# SPDX-FileCopyrightText: 2026 Shin
# SPDX-License-Identifier: Apache-2.0
import logging

import pytest

from fosslight_util import set_log


@pytest.fixture
def file_logger(tmp_path, monkeypatch):
    logger = logging.getLogger(f"{__name__}.{tmp_path.name}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    monkeypatch.setattr(set_log.constant, "LOGGER_NAME", logger.name)
    original_path = tmp_path / "original.log"
    handler = logging.FileHandler(original_path, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.info("before relocation")
    try:
        yield logger, original_path
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()


def assert_file_logging_settings(logger):
    handlers = [handler for handler in logger.handlers if isinstance(handler, logging.FileHandler)]
    assert len(handlers) == 1
    assert handlers[0].level == logging.INFO
    assert handlers[0].formatter._fmt == "%(levelname)s: %(message)s"


@pytest.mark.parametrize("failure", ["parent_is_file", "mkdir_denied", "move_denied"])
def test_failed_log_relocation_keeps_logging_and_allows_retry(file_logger, tmp_path, monkeypatch, failure):
    logger, original_path = file_logger
    destination_dir = tmp_path / "output"
    final_path = destination_dir / "final.log"
    if failure == "parent_is_file":
        destination_dir.write_text("existing file", encoding="utf-8")

    def denied(*args, **kwargs):
        raise PermissionError("relocation denied")

    with monkeypatch.context() as patch:
        if failure == "mkdir_denied":
            patch.setattr(set_log.os, "makedirs", denied)
        elif failure == "move_denied":
            patch.setattr(set_log.shutil, "move", denied)
        with pytest.raises(OSError):
            set_log.move_log_file(original_path, final_path)

    logger.warning("after failure: 한글")
    assert "WARNING: after failure: 한글" in original_path.read_text(encoding="utf-8")
    assert not final_path.exists()
    assert_file_logging_settings(logger)

    if failure == "parent_is_file":
        assert destination_dir.read_text(encoding="utf-8") == "existing file"
        destination_dir.unlink()
    set_log.move_log_file(original_path, final_path)
    logger.error("after retry")
    contents = final_path.read_text(encoding="utf-8")
    assert "INFO: before relocation" in contents
    assert "WARNING: after failure: 한글" in contents
    assert "ERROR: after retry" in contents
    assert not original_path.exists()
    assert_file_logging_settings(logger)


def test_successful_log_relocation_preserves_messages_and_settings(file_logger, tmp_path):
    logger, original_path = file_logger
    final_path = tmp_path / "output" / "final.log"
    set_log.move_log_file(original_path, final_path)
    logger.info("after relocation: 한글")
    logger.debug("below file log level")
    contents = final_path.read_text(encoding="utf-8")
    assert "INFO: before relocation" in contents
    assert "INFO: after relocation: 한글" in contents
    assert "below file log level" not in contents
    assert not original_path.exists()
    assert_file_logging_settings(logger)
