#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
from fosslight_util.write_excel import write_result_to_excel, write_result_to_csv
from fosslight_util.write_opossum import write_opossum
from fosslight_util.write_yaml import write_yaml
from typing import Tuple

SUPPORT_FORMAT = {'excel': '.xlsx', 'csv': '.csv', 'opossum': '.json', 'yaml': '.yaml'}


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
            msg = 'Enter the supported format with -f option: ' + ', '.join(list(support_format.keys()))
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
                        msg = f"Enter the same extension of output file(-o:'{output}') with format(-f:'{format}')."
                else:
                    if basename_extension not in support_format.values():
                        success = False
                        msg = 'Enter the supported file extension: ' + ', '.join(list(support_format.values()))
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
                msg = 'Enter the supported format with -f option: ' + ', '.join(list(support_format.keys()))
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
                        msg = f"The format of output file(-o:'{output}') should be in the format list(-f:'{formats}')."
                else:
                    if basename_extension not in support_format.values():
                        success = False
                        msg = 'Enter the supported file extension: ' + ', '.join(list(support_format.values()))
                    output_extensions.append(basename_extension)
                output_files = [basename_file for _ in range(len(output_extensions))]
            else:
                output_path = output
    if not output_extensions:
        output_extensions = ['.xlsx']

    return success, msg, output_path, output_files, output_extensions


def write_output_file(output_file_without_ext: str, file_extension: str, scan_item, extended_header: dict = {},
                      hide_header: dict = {}) -> Tuple[bool, str, str]:
    success = True
    msg = ''

    if file_extension == '':
        file_extension = '.xlsx'
    result_file = output_file_without_ext + file_extension

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
        msg = f'Not supported file extension({file_extension})'

    return success, msg, result_file
