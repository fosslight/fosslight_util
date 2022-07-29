#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
from fosslight_util.write_excel import write_result_to_excel, write_result_to_csv, remove_empty_sheet
from fosslight_util.write_opossum import write_opossum
from fosslight_util.write_yaml import write_yaml

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
            msg = 'Add the supported format with -f option: ' + ', '.join(list(support_format.keys()))
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
                find_ext = False
                for _format, _ext in support_format.items():
                    if basename_extension == _ext:
                        find_ext = True
                        if format:
                            if _format != format:
                                success = False
                                msg = 'Enter the same extension of output file(-o:' + output + ') with format(-f:' + format + ').'
                        if success:
                            output_file = basename_file
                            output_extension = _ext
                if not find_ext:
                    success = False
                    msg = 'Enter the supported file extension: ' + ', '.join(list(support_format.values()))
            else:
                output_path = output

    return success, msg, output_path, output_file, output_extension


def write_output_file(output_file_without_ext, file_extension, sheet_list, extended_header={}):
    success = True
    msg = ''

    is_not_null, sheet_list = remove_empty_sheet(sheet_list)
    if is_not_null:
        if file_extension == '':
            file_extension = '.xlsx'
        result_file = output_file_without_ext + file_extension

        if file_extension == '.xlsx':
            success, msg = write_result_to_excel(result_file, sheet_list, extended_header)
        elif file_extension == '.csv':
            success, msg, result_file = write_result_to_csv(result_file, sheet_list)
        elif file_extension == '.json':
            success, msg = write_opossum(result_file, sheet_list)
        elif file_extension == '.yaml':
            success, msg, result_file = write_yaml(result_file, sheet_list, False)
        else:
            success = False
            msg = f'Not supported file extension({file_extension})'
    else:
        result_file = ""
        msg = "Nothing is detected from the scanner so output file is not generated."

    return success, msg, result_file
