#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import fnmatch
from typing import List

EXCLUDE_DIRECTORY = ["test", "tests", "doc", "docs", "intermediates"]
PACKAGE_DIRECTORY = ["node_modules", "venv", "Pods", "Carthage"]
EXCLUDE_FILENAME = ["changelog", "config.guess", "config.sub", "changes", "ltmain.sh",
                    "configure", "configure.ac", "depcomp", "compile", "missing", "makefile",
                    'fosslight_bin', 'fosslight_bin.exe']
EXCLUDE_FILE_EXTENSION = ['qm', 'xlsx', 'pdf', 'pptx', 'jfif', 'docx', 'doc', 'whl',
                          'xls', 'xlsm', 'ppt', 'mp4', 'pyc', 'plist', 'dat',
                          "m4", "in", "po", "class"]


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


def _has_parent_in_exclude_list(rel_path: str, path_to_exclude: list) -> bool:
    path_parts = rel_path.replace('\\', '/').split('/')
    for i in range(1, len(path_parts)):
        parent_path = '/'.join(path_parts[:i])
        if parent_path in path_to_exclude:
            return True
    return False


def is_exclude_dir(rel_path: str) -> tuple:
    dir_name = os.path.basename(rel_path).replace('\\', '/')
    if '/' in dir_name:
        dir_name = dir_name.split('/')[-1]

    if dir_name.startswith('.'):
        return True, True

    dir_name_lower = dir_name.lower()

    for exclude_dir in EXCLUDE_DIRECTORY:
        if dir_name_lower == exclude_dir.lower():
            return True, False

    for package_dir in PACKAGE_DIRECTORY:
        if dir_name_lower == package_dir.lower():
            return True, False

    return False, False


def get_excluded_paths(path_to_scan: str, custom_excluded_paths: list = [], custom_exclude_extension: list = []) -> tuple:
    path_to_exclude = []
    path_to_exclude_with_dot = []
    excluded_files = set()  # Use set for O(1) operations
    abs_path_to_scan = os.path.abspath(path_to_scan)
    custom_excluded_normalized = [p.replace('\\', '/') for p in custom_excluded_paths]
    cnt_file_except_skipped = 0

    for root, dirs, files in os.walk(path_to_scan):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            rel_path = os.path.relpath(dir_path, abs_path_to_scan).replace('\\', '/')
            if not _has_parent_in_exclude_list(rel_path, path_to_exclude):
                is_exclude, has_dot = is_exclude_dir(rel_path)
                if is_exclude:
                    path_to_exclude.append(rel_path)
                    if has_dot:
                        path_to_exclude_with_dot.append(rel_path)
                elif rel_path in custom_excluded_normalized or rel_path + '/' in custom_excluded_normalized:
                    path_to_exclude.append(rel_path)

        for file_name in files:
            file_path = os.path.join(root, file_name)
            rel_path = os.path.relpath(file_path, abs_path_to_scan).replace('\\', '/')
            should_exclude = False
            except_info_sheet = False
            if not _has_parent_in_exclude_list(rel_path, path_to_exclude):
                file_ext = os.path.splitext(file_name)[1].lstrip('.').lower()
                if rel_path in custom_excluded_normalized:
                    should_exclude = True
                elif file_name in custom_excluded_normalized:
                    should_exclude = True
                elif file_name.startswith('.'):
                    should_exclude = True
                    except_info_sheet = True
                elif file_ext and file_ext in custom_exclude_extension:
                    should_exclude = True
                elif file_name.lower() in EXCLUDE_FILENAME:
                    should_exclude = True
                    except_info_sheet = True
                    cnt_file_except_skipped += 1
                elif file_ext and file_ext in EXCLUDE_FILE_EXTENSION:
                    should_exclude = True
                    except_info_sheet = True
                    cnt_file_except_skipped += 1

                if should_exclude:
                    path_to_exclude.append(rel_path)
                    if except_info_sheet:
                        path_to_exclude_with_dot.append(rel_path)
                    excluded_files.add(rel_path)
            else:
                should_exclude = True
                excluded_files.add(rel_path)
            if not should_exclude:
                cnt_file_except_skipped += 1

    path_to_exclude_without_dot = list(set(path_to_exclude) - set(path_to_exclude_with_dot))
    return path_to_exclude, path_to_exclude_without_dot, list(excluded_files), cnt_file_except_skipped
