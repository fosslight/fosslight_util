# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

from fosslight_util.download import rewrite_alpha_gnu_mirror

_ALPHA = "https://alpha.gnu.org/gnu/autoconf/autoconf-2.72e.tar.gz"
_MIRROR = (
    "https://ftp.mirrorservice.org/sites/alpha.gnu.org/gnu/autoconf/"
    "autoconf-2.72e.tar.gz"
)


def test_rewrites_alpha_gnu_to_alpha_tree_mirror():
    assert rewrite_alpha_gnu_mirror(_ALPHA) == _MIRROR
    assert rewrite_alpha_gnu_mirror(
        "http://alpha.gnu.org/gnu/autoconf/autoconf-2.72e.tar.gz"
    ) == _MIRROR


def test_leaves_other_hosts_unchanged():
    stable = "https://ftp.gnu.org/gnu/autoconf/autoconf-2.72.tar.xz"
    assert rewrite_alpha_gnu_mirror(stable) == stable
    assert rewrite_alpha_gnu_mirror(_MIRROR) == _MIRROR
