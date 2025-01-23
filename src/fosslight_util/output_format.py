#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import platform
from fosslight_util.write_excel import write_result_to_excel, write_result_to_csv
from fosslight_util.write_opossum import write_opossum
from fosslight_util.write_yaml import write_yaml
from fosslight_util.write_spdx import write_spdx
from fosslight_util.write_cyclonedx import write_cyclonedx
from typing import Tuple

SUPPORT_FORMAT = {'excel': '.xlsx', 'csv': '.csv', 'opossum': '.json', 'yaml': '.yaml',
                  'spdx-yaml': '.yaml', 'spdx-json': '.json', 'spdx-xml': '.xml',
                  'spdx-tag': '.tag', 'cyclonedx-json': '.json', 'cyclonedx-xml': '.xml'}


def check_output_format(output='', format='', customized_format={}):
    success = True
    msg = ''
    output_path = ''
    output_file = ''
    output_extension = ''

    if customized_format:
        support_format = customized_format
    else:
        support_format = SUPPORT_FORMAT

    if format:
        format = format.lower()
        if format not in list(support_format.keys()):
            success = False
            msg = '(-f option) Enter the supported format: ' + ', '.join(list(support_format.keys()))
        else:
            output_extension = support_format[format]

    if success:
        if output != '':
            basename_extension = ''
            if not os.path.isdir(output):
                output_path = os.path.dirname(output)

                basename = os.path.basename(output)
                basename_file, basename_extension = os.path.splitext(basename)
            if basename_extension:
                if format:
                    if output_extension != basename_extension:
                        success = False
                        msg = f"(-o & -f option) Enter the same extension of output file(-o:'{output}') \
                                with format(-f:'{format}')."
                else:
                    if basename_extension not in support_format.values():
                        success = False
                        msg = '(-o option) Enter the supported file extension: ' + ', '.join(list(support_format.values()))
                if success:
                    output_file = basename_file
                    output_extension = basename_extension
            else:
                output_path = output

    return success, msg, output_path, output_file, output_extension


def check_output_formats(output='', formats=[], customized_format={}):
    success = True
    msg = ''
    output_path = ''
    output_files = []
    output_extensions = []

    if customized_format:
        support_format = customized_format
    else:
        support_format = SUPPORT_FORMAT

    if formats:
        # If -f option exist
        formats = [format.lower() for format in formats]
        for format in formats:
            if format not in list(support_format.keys()):
                success = False
                msg = '(-f option) Enter the supported format: ' + ', '.join(list(support_format.keys()))
            else:
                output_extensions.append(support_format[format])

    if success:
        if output != '':
            basename_extension = ''
            if not os.path.isdir(output):
                output_path = os.path.dirname(output)

                basename = os.path.basename(output)
                basename_file, basename_extension = os.path.splitext(basename)
            if basename_extension:
                if formats:
                    if basename_extension not in output_extensions:
                        success = False
                        msg = f"(-o & -f option) The format of output file(-o:'{output}') \
                                should be in the format list(-f:'{formats}')."
                else:
                    if basename_extension not in support_format.values():
                        success = False
                        msg = '(-o option) Enter the supported file extension: ' + ', '.join(list(support_format.values()))
                    output_extensions.append(basename_extension)
                output_files = [basename_file for _ in range(len(output_extensions))]
            else:
                output_path = output
    if not output_extensions:
        output_extensions = ['.xlsx']

    return success, msg, output_path, output_files, output_extensions


def check_output_formats_v2(output='', formats=[], customized_format={}):
    success = True
    msg = ''
    output_path = ''
    output_files = []
    output_extensions = []

    if customized_format:
        support_format = customized_format
    else:
        support_format = SUPPORT_FORMAT

    if formats:
        # If -f option exist
        formats = [format.lower() for format in formats]
        for format in formats:
            if format not in list(support_format.keys()):
                success = False
                msg = '(-f option) Enter the supported format with -f option: ' + ', '.join(list(support_format.keys()))
            else:
                output_extensions.append(support_format[format])

    if success:
        if output != '':
            basename_extension = ''
            if not os.path.isdir(output):
                output_path = os.path.dirname(output)

                basename = os.path.basename(output)
                basename_file, basename_extension = os.path.splitext(basename)
            if basename_extension:
                if formats:
                    if basename_extension not in output_extensions:
                        success = False
                        msg = f"(-o & -f option) The format of output file(-o:'{output}') \
                                should be in the format list(-f:'{formats}')."
                else:
                    if basename_extension not in support_format.values():
                        success = False
                        msg = '(-o option) Enter the supported file extension: ' + ', '.join(list(support_format.values()))
                    output_extensions.append(basename_extension)
                output_files = [basename_file for _ in range(len(output_extensions))]
            else:
                output_path = output
    if not output_extensions:
        output_extensions = ['.xlsx']
    if not formats:
        formats = []
        for ext in output_extensions:
            for key, value in support_format.items():
                if value == ext:
                    formats.append(key)
                    break
    return success, msg, output_path, output_files, output_extensions, formats


def write_output_file(output_file_without_ext: str, file_extension: str, scan_item, extended_header: dict = {},
                      hide_header: dict = {}, format: str = '', spdx_version: str = '2.3') -> Tuple[bool, str, str]:
    success = True
    msg = ''

    if file_extension == '':
        file_extension = '.xlsx'
    result_file = output_file_without_ext + file_extension

    if format:
        if format == 'excel':
            success, msg = write_result_to_excel(result_file, scan_item, extended_header, hide_header)
        elif format == 'csv':
            success, msg, _ = write_result_to_csv(result_file, scan_item, False, extended_header)
        elif format == 'opossum':
            success, msg = write_opossum(result_file, scan_item)
        elif format == 'yaml':
            success, msg, _ = write_yaml(result_file, scan_item, False)
        elif format.startswith('spdx') or format.startswith('cyclonedx'):
            if platform.system() == 'Windows' or platform.system() == 'Darwin':
                success = False
                msg = f'{platform.system()} not support spdx format.'
            else:
                if format.startswith('spdx'):
                    success, msg, _ = write_spdx(output_file_without_ext, file_extension, scan_item, spdx_version)
                elif format.startswith('cyclonedx'):
                    success, msg, _ = write_cyclonedx(output_file_without_ext, file_extension, scan_item)
    else:
        if file_extension == '.xlsx':
            success, msg = write_result_to_excel(result_file, scan_item, extended_header, hide_header)
        elif file_extension == '.csv':
            success, msg, result_file = write_result_to_csv(result_file, scan_item, False, extended_header)
        elif file_extension == '.json':
            success, msg = write_opossum(result_file, scan_item)
        elif file_extension == '.yaml':
            success, msg, result_file = write_yaml(result_file, scan_item, False)
        else:
            success = False
            msg = f'(-f option) Not supported file extension({file_extension})'

    return success, msg, result_file
