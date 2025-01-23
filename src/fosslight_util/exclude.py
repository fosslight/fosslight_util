#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import fnmatch
from typing import List


def excluding_files(patterns: List[str], path_to_scan: str) -> List[str]:
    excluded_paths = set()

    # Normalize patterns: e.g., 'sample/', 'sample/*' -> 'sample'
    # Replace backslash with slash
    normalized_patterns = []
    for pattern in patterns:
        pattern = pattern.replace('\\', '/')
        if pattern.endswith('/') or pattern.endswith('/*'):
            pattern = pattern.rstrip('/*')
        normalized_patterns.append(pattern)

    # Traverse directories
    for root, dirs, files in os.walk(path_to_scan):
        remove_dir_list = []

        # (1) Directory matching
        for d in dirs:
            dir_name = d
            dir_path = os.path.relpath(os.path.join(root, d), path_to_scan).replace('\\', '/')
            matched = False

            for pat in normalized_patterns:
                # Match directory name
                if fnmatch.fnmatch(dir_name, pat):
                    matched = True

                # Match the full relative path
                if not matched:
                    if fnmatch.fnmatch(dir_path, pat) or fnmatch.fnmatch(dir_path, pat + "/*"):
                        matched = True

                # If matched, exclude all files under this directory and stop checking patterns
                if matched:
                    sub_root_path = os.path.join(root, d)
                    for sr, _, sf in os.walk(sub_root_path):
                        for sub_file in sf:
                            sub_file_path = os.path.relpath(os.path.join(sr, sub_file), path_to_scan)
                            excluded_paths.add(sub_file_path.replace('\\', '/'))
                    remove_dir_list.append(d)
                    break

        # (1-2) Prune matched directories from further traversal
        for rd in remove_dir_list:
            dirs.remove(rd)

        # (2) File matching
        for f in files:
            file_path = os.path.relpath(os.path.join(root, f), path_to_scan).replace('\\', '/')
            for pat in normalized_patterns:
                if fnmatch.fnmatch(file_path, pat) or fnmatch.fnmatch(file_path, pat + "/*"):
                    excluded_paths.add(file_path)
                    break

    return sorted(excluded_paths)
