#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
from fosslight_util.write_excel import write_result_to_excel, write_excel_and_csv, write_result_to_csv
from fosslight_util.write_opossum import write_opossum

SUPPORT_FORMAT = {'excel': '.xlsx', 'csv': '.csv', 'opossum': '.json'}


def check_output_format(output='', format=''):
    success = True
    msg = ''
    output_path = ''
    output_file = ''
    output_extension = ''

    if format:
        format = format.lower()
        if format not in list(SUPPORT_FORMAT.keys()):
            success = False
            msg = 'Add the supported format with -f option: ' + ', '.join(list(SUPPORT_FORMAT.keys()))
        else:
            output_extension = SUPPORT_FORMAT[format]

    if success:
        if output != '':
            output_path = os.path.dirname(output)

            basename = os.path.basename(output)
            basename_file, basename_extension = os.path.splitext(basename)
            if basename_extension:
                find_ext = False
                for _format, _ext in SUPPORT_FORMAT.items():
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
                    msg = 'Enter the supported file extension: ' + ', '.join(list(SUPPORT_FORMAT.values()))
            else:
                output_path = output

    return success, msg, output_path, output_file, output_extension


def write_output_file(output_file_without_ext, file_extension, sheet_list, extended_header={}):
    success = True
    msg = ''

    if file_extension == '':
        success, msg = write_excel_and_csv(output_file_without_ext, sheet_list, False, extended_header)
    elif file_extension == '.xlsx':
        success, msg = write_result_to_excel(output_file_without_ext + file_extension, sheet_list, extended_header)
    elif file_extension == '.csv':
        success, msg = write_result_to_csv(output_file_without_ext + file_extension, sheet_list)
    elif file_extension == '.json':
        success, msg = write_opossum(output_file_without_ext + file_extension, sheet_list)
    else:
        success = False
        msg = 'Not supported file extension(' + file_extension + ')'

    return success, msg
