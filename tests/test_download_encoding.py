# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Child process output must be decoded as UTF-8, whatever the system locale is.

Without an explicit encoding, text=True decodes with the locale encoding (cp949 on
Korean Windows). git writes UTF-8, so a path with Hangul in it raised
UnicodeDecodeError in subprocess' reader thread and git's error message was lost.
The failure needs a non-UTF-8 locale, which CI does not have, so check the calls.
"""

import ast
from pathlib import Path

import fosslight_util.download as download


def _text_mode_calls():
    tree = ast.parse(Path(download.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        kwargs = {k.arg: k.value for k in node.keywords if k.arg}
        if any(isinstance(kwargs.get(name), ast.Constant) and kwargs[name].value is True
               for name in ("text", "universal_newlines")):
            yield node.lineno, kwargs


def test_text_mode_subprocess_calls_decode_utf8_without_failing():
    calls = list(_text_mode_calls())
    assert calls, "expected text-mode subprocess calls in download.py"

    wrong = [
        lineno for lineno, kwargs in calls
        if not (isinstance(kwargs.get("encoding"), ast.Constant) and kwargs["encoding"].value == "utf-8"
                and isinstance(kwargs.get("errors"), ast.Constant) and kwargs["errors"].value == "replace")
    ]
    assert not wrong, f'download.py lines {wrong}: add encoding="utf-8", errors="replace"'
