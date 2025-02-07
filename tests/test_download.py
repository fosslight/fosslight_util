# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import pytest

from fosslight_util.download import cli_download_and_extract, download_git_clone
from tests import constants


def test_download_from_github():
    # given
    git_url = "https://github.com/LGE-OSS/example"
    target_dir = os.path.join(constants.TEST_RESULT_DIR, "download/example")
    log_dir = "test_result/download_log/example"

    # when
    success, _, _, _ = cli_download_and_extract(git_url, target_dir, log_dir)

    # then
    assert success is True
    assert len(os.listdir(target_dir)) > 0


@pytest.mark.parametrize("git_url",
                         ["git://git.kernel.org/pub/scm/utils/kernel/kmod/kmod.git;protocol=git;branch=hash-stat2",
                          "git://git.kernel.org/pub/scm/utils/kernel/kmod/kmod.git;protocol=git;tag=v32"])
def test_download_from_github_with_branch_or_tag(git_url):
    # given
    target_dir = os.path.join(constants.TEST_RESULT_DIR, "download/example")
    log_dir = "test_result/download_log/example"

    # when
    success, _, _, _ = cli_download_and_extract(git_url, target_dir, log_dir)

    # then
    assert success is True
    assert len(os.listdir(target_dir)) > 0


@pytest.mark.parametrize("project_name, project_url",
                         [("filelock", "https://pypi.org/project/filelock/3.4.1"),
                          ("dependency", "https://pypi.org/project/fosslight-dependency/3.0.5/"),
                          ("jackson", "https://mvnrepository.com/artifact/com.fasterxml.jackson.core/jackson-databind/2.12.2"),
                          ("pub", "https://pub.dev/packages/file/versions/5.2.1")])
def test_download_from_wget(project_name, project_url):
    # given
    target_dir = os.path.join(constants.TEST_RESULT_DIR,
                              os.path.join("download", project_name))
    log_dir = os.path.join(constants.TEST_RESULT_DIR,
                           os.path.join("download_log" + project_name))

    # when
    success, _, _, _ = cli_download_and_extract(project_url, target_dir, log_dir)

    # then
    assert success is True
    assert len(os.listdir(target_dir)) > 0


def test_download_git_clone_with_branch():
    # given
    git_url = "git://git.kernel.org/pub/scm/utils/kernel/kmod/kmod.git"
    target_dir = os.path.join(constants.TEST_RESULT_DIR, "download/example")
    branch_name = "hash-stat2"

    # when
    success, _, oss_name, oss_version = download_git_clone(git_url, target_dir, "", "", branch_name)

    # then
    assert success is True
    assert len(os.listdir(target_dir)) > 0
    assert oss_name == ''
    assert oss_version == branch_name


def test_download_git_clone_with_tag():
    # given
    git_url = "git://git.kernel.org/pub/scm/utils/kernel/kmod/kmod.git"
    target_dir = os.path.join(constants.TEST_RESULT_DIR, "download/example")
    tag_name = "v32"

    # when
    success, _, oss_name, oss_version = download_git_clone(git_url, target_dir, "", tag_name)

    # then
    assert success is True
    assert len(os.listdir(target_dir)) > 0
    assert oss_name == ''
    assert oss_version == tag_name


def test_download_main_branch_when_any_branch_or_tag_not_entered():
    # given
    git_url = "https://github.com/LGE-OSS/example"
    target_dir = os.path.join(constants.TEST_RESULT_DIR, "download/example")
    expected_oss_ver = ""

    # when
    success, _, oss_name, oss_version = download_git_clone(git_url, target_dir)

    # then
    assert success is True
    assert len(os.listdir(target_dir)) > 0
    assert oss_name == 'LGE-OSS-example'
    assert oss_version == expected_oss_ver


def test_download_main_branch_when_non_existent_branch_entered():
    # given
    git_url = "https://github.com/LGE-OSS/example"
    target_dir = os.path.join(constants.TEST_RESULT_DIR, "download/example")
    branch_name = "non-existent-branch"
    expected_oss_ver = ""

    # when
    success, _, oss_name, oss_version = download_git_clone(git_url, target_dir, "", "", branch_name)

    # then
    assert success is True
    assert len(os.listdir(target_dir)) > 0
    assert oss_name == 'LGE-OSS-example'
    assert oss_version == expected_oss_ver


def test_download_main_branch_when_non_existent_tag_entered():
    # given
    git_url = "https://github.com/LGE-OSS/example"
    target_dir = os.path.join(constants.TEST_RESULT_DIR, "download/example")
    tag_name = "non-existent-tag"
    expected_oss_ver = ""

    # when
    success, _, oss_name, oss_version = download_git_clone(git_url, target_dir, "", tag_name)

    # then
    assert success is True
    assert len(os.listdir(target_dir)) > 0
    assert oss_name == 'LGE-OSS-example'
    assert oss_version == expected_oss_ver
