# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for git checkout ref resolution (decide_checkout)."""

from pathlib import Path

import pytest

from fosslight_util.download import (
    _repo_name_from_git_url,
    _repo_prefixed_version_refs,
    _try_resolve_checkout_base,
    clarified_version_from_oss_version,
    decide_checkout,
    download_git_clone,
)


@pytest.mark.parametrize(
    "git_url,expected",
    [
        ("https://github.com/rrousselGit/freezed", "freezed"),
        ("https://github.com/rrousselGit/freezed.git", "freezed"),
        ("git@github.com:rrousselGit/freezed.git", "freezed"),
    ],
)
def test_repo_name_from_git_url(git_url, expected):
    assert _repo_name_from_git_url(git_url) == expected


def test_repo_prefixed_version_refs():
    assert _repo_prefixed_version_refs("freezed", "2.4.4") == [
        "freezed-v2.4.4",
        "freezed-v.2.4.4",
        "freezed_2.4.4",
        "freezed-2.4.4",
    ]
    assert _repo_prefixed_version_refs("freezed", "v2.4.4")[0] == "freezed-v2.4.4"


def test_try_resolve_checkout_base_matches_repo_prefixed_tag():
    ref_set = {"freezed-v2.4.4", "freezed_annotation-v2.4.4", "master"}
    ref, clar = _try_resolve_checkout_base("freezed-v2.4.4", ref_set)
    assert ref == "freezed-v2.4.4"
    assert clar == "2.4.4"


def test_try_resolve_checkout_base_semver_matches_repo_prefixed_tag():
    ref_set = {"freezed-v2.4.4", "freezed_annotation-v2.4.4", "master"}
    ref, clar = _try_resolve_checkout_base("2.4.4", ref_set)
    assert ref == "freezed-v2.4.4"
    assert clar == "2.4.4"


def test_clarified_version_from_repo_prefixed_tag():
    assert clarified_version_from_oss_version("freezed-v2.4.4") == "2.4.4"


def test_clarified_version_from_android_tag():
    assert clarified_version_from_oss_version("android-15.0.0_r1") == "15.0.0"


def test_try_resolve_checkout_base_android_two_part_hint():
    """-c 15.0 must clarify 15.0.0 from the matched android-15.0.0_* tag, not 15.0."""
    ref_set = {
        "android-15.0.0_r1",
        "android-15.0.0_r2",
        "android-15.0.0_r10",
        "android-14.0.0_r1",
        "main",
    }
    ref, clar = _try_resolve_checkout_base("15.0", ref_set)
    assert ref == "android-15.0.0_r1"
    assert clar == "15.0.0"


def test_try_resolve_checkout_base_omitted_patch_uses_ref_version():
    ref_set = {"v1.0.5", "v1.0.3", "master"}
    ref, clar = _try_resolve_checkout_base("1.0", ref_set)
    assert ref == "v1.0.5"
    assert clar == "1.0.5"


def test_decide_checkout_android_two_part_hint(monkeypatch):
    tags = ["android-15.0.0_r1", "android-15.0.0_r2", "android-15.0.0_r10"]
    monkeypatch.setattr(
        "fosslight_util.download.get_remote_refs",
        lambda _url: {"tags": tags, "branches": ["main"]},
    )

    ref, clar = decide_checkout(
        checkout_to="15.0",
        git_url="https://android.googlesource.com/platform/system/libhwbinder",
    )

    assert ref == "android-15.0.0_r1"
    assert clar == "15.0.0"


def test_download_git_clone_android_libhwbinder_c_15_0(tmp_path, monkeypatch):
    """https://android.googlesource.com/platform/system/libhwbinder -c 15.0."""
    tags = ["android-15.0.0_r1", "android-15.0.0_r2", "android-15.0.0_r10"]
    monkeypatch.setattr(
        "fosslight_util.download.get_remote_refs",
        lambda _url: {"tags": tags, "branches": ["main"]},
    )
    monkeypatch.setattr("fosslight_util.download._start_download_watchdog", lambda: None)
    monkeypatch.setattr(
        "fosslight_util.download._cancel_download_watchdog", lambda alarm=None: None
    )

    def fake_download_git_repository(refs_to_checkout, git_url, target_dir, *args, **kwargs):
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        (Path(target_dir) / "README").write_text("ok")
        return True, refs_to_checkout or "", ""

    monkeypatch.setattr(
        "fosslight_util.download.download_git_repository",
        fake_download_git_repository,
    )

    success, _, _, oss_version, clarified_version = download_git_clone(
        "https://android.googlesource.com/platform/system/libhwbinder",
        str(tmp_path / "libhwbinder"),
        "15.0",
    )

    assert success is True
    assert oss_version == "android-15.0.0_r1"
    assert clarified_version == "15.0.0"


def test_decide_checkout_resolves_repo_prefixed_tag(monkeypatch):
    tags = ["freezed-v2.4.4", "freezed_annotation-v2.4.4"]
    monkeypatch.setattr(
        "fosslight_util.download.get_remote_refs",
        lambda _url: {"tags": tags, "branches": ["master"]},
    )

    ref, clar = decide_checkout(
        checkout_to="2.4.4",
        git_url="https://github.com/rrousselGit/freezed",
    )

    assert ref == "freezed-v2.4.4"
    assert clar == "2.4.4"
