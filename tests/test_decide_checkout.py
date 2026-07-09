# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for git checkout ref resolution (decide_checkout)."""

import pytest

from fosslight_util.download import (
    _repo_name_from_git_url,
    _repo_prefixed_version_refs,
    _try_resolve_checkout_base,
    clarified_version_from_oss_version,
    decide_checkout,
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
