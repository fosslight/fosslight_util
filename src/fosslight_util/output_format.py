#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
from fosslight_util.write_excel import write_result_to_excel, write_result_to_csv, remove_empty_sheet
from fosslight_util.write_opossum import write_opossum
from fosslight_util.write_yaml import write_yaml

SUPPORT_FORMAT = {'excel': '.xlsx', 'csv': '.csv', 'opossum': '.json', 'yaml': '.yaml'}


# def check_output_format(output='', format='', customized_format={}):
def check_output_format(outputs=[], formats=[], customized_format={}):
    success = True
    msg = ''
    output_paths = []
    output_files = []
    # output_extension = ''
    output_extensions = []
    basename_files =[]
    basename_extensions = []

    if customized_format:
        support_format = customized_format
    else:
        support_format = SUPPORT_FORMAT

    if formats:
        formats = [format.lower() for format in formats]
        print("in Util_output_format_Type : ", type(formats), " | Value of formats: ", formats)
        # formats = formats.lower()
        for format in formats:
            if format not in list(support_format.keys()):
                success = False
                msg = 'Enter the supported format with -f option: ' + ', '.join(list(support_format.keys()))
            else:
                output_extensions.append(support_format[format])
        print("!!!extentions : ", output_extensions)

    if success:  # formats에서 support에 해당하지 않는 format이 없으면
        if output != '':  # output이 있으면
            basename_extension = ''
            if not os.path.isdir(output):  # directory 명이 아니면
                output_path = os.path.dirname(output)

                basename = os.path.basename(output)
                basename_file, basename_extension = os.path.splitext(basename)  # file과 extension 분리
            if basename_extension:  # extension이 있으면
                if format:  # format이 있으면
                    if output_extension != basename_extension:
                        success = False
                        msg = f"Enter the same extension of output file(-o:'{output}') with format(-f:'{format}')."
                else:  # format이 없으면
                    if basename_extension not in support_format.values():
                        success = False
                        msg = 'Enter the supported file extension: ' + ', '.join(list(support_format.values()))
                if success:  # format이 없거나, output과 일치하면
                    output_file = basename_file
                    output_extension = basename_extension
            else: # output이 directory명이면 
                output_path = output
    if success:  # formats에서 support에 해당하지 않는 format이 없으면
        if outputs: # output이 있으면
            if len(outputs) < 2:  # 인자가 1개일 때
                print("!!!!output 11111!!!!")
            else:
                for index, output in enumerate(outputs):
                    basename_extension = ''
                    if not os.path.isdir(output):
                        output_paths.append(os.path.dirname(output))

                        basename = os.path.basename(output)
                        basename_file, basename_extension = os.path.splitext(basename)
                    if basename_extension:
                        if formats:
                            if output_extensions[index] != basename_extension:
                                success = False
                                msg = f"Enter the same extension of output file(-o:'{outputs}') with format(-f:'{formats}')."
                        else:
                            if basename_extension not in support_format.values():
                                success = False
                                msg = 'Enter the supported file extension: ' + ', '.join(list(support_format.values()))
                        if success:
                            output_files.append(basename_file)
                            output_extensions.append(basename_extension)
                        if success:
                            output_files.append(basename_file)
                            output_extensions.append(basename_extension)
                    else:
                        output_paths


        if outputs:
            for output in outputs:
                basename_extension = ''
                if not os.path.isdir(output):
                    output_paths.append(os.path.dirname(output))

                    basename = os.path.basename(output)
                    basename_file, basename_extension = os.path.splitext(basename)
                if basename_extension:
                    if formats:
                        if output_extensions != basename_extension:
                            success = False
                            msg = f"Enter the same extension of output file(-o:'{outputs}') with format(-f:'{formats}')."
                    else:
                        if basename_extension not in support_format.values():
                            success = False
                            msg = 'Enter the supported file extension: ' + ', '.join(list(support_format.values()))
                    if success:
                        output_file = basename_file
                        output_extensions = basename_extension
                else:
                    output_paths = outputs

    return success, msg, output_paths, output_file, output_extensions


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
