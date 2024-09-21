import os
import pytest
from fosslight_util.write_excel import write_excel_and_csv
from fosslight_util.output_format import write_output_file

# legacy/test_excel_and_csv

def test_write_excel_and_csv(sheet_list_fixture):
    #given
    output_dir = "test_result/excel_and_csv"
    result_file_name = "FOSSLight-Report"
    file_to_create = os.path.join(output_dir, result_file_name)

    include_tab_name = sheet_list_fixture[0]
    sheet_contents = sheet_list_fixture[1]

    not_included_tab_name = 'SRC_NULL'
    sheet_contents[not_included_tab_name] = []

    #when
    success, msg, result_file = write_excel_and_csv(file_to_create, sheet_contents)

    #then
    assert success is True
    assert all(item in result_file for item in include_tab_name)
    assert result_file_name in result_file
    assert not_included_tab_name not in result_file

# legacy/test_output_format

@pytest.mark.parametrize("output_dir, result_file_name, file_extension",
    [("test_result/excel_and_csv/excel", "Test_Excel", ".xlsx"),
     ("test_result/excel_and_csv/csv", "Test_Csv", ".csv"),
     ("test_result/output_format", "FL-TEST_opossum", ".json")])
def test_write_output_file(output_dir, result_file_name, file_extension):
    #given
    file_to_create = os.path.join(output_dir, result_file_name)

    sheet_contents = {}
    src_tab_name = 'SRC'
    src_sheet_items = [['run_scancode.py', 'fosslight_source',
                        '3.0.6', 'Apache-2.0',  'https://github.com/LGE-OSS/fosslight_source',
                        'https://github.com/LGE-OSS/fosslight_source',
                        'Copyright (c) 2021 LG Electronics, Inc.',
                        'Exclude', 'Comment message'],
                       ['', 'Enact',
                        '', 'Apache-2.0',  'https://github.com/enactjs/enact',
                        'https://enactjs.com', 'Copyright (c) 2012-2021 LG Electronics',
                        '', ''],
                       ['dependency_unified.py', 'fosslight_dependency',
                        '3.0.6', 'Apache-2.0',  'https://github.com/LGE-OSS/fosslight_dependency',
                        'https://github.com/LGE-OSS/fosslight_dependency',
                        'Copyright (c) 2020 LG Electronics, Inc.',
                        '', '']]
    bin_tab_name = 'BIN_TEST'
    bin_sheet_items = [['dependency_unified.py', 'fosslight_dependency',
                        '3.0.6', 'Apache-2.0',  'https://github.com/LGE-OSS/fosslight_dependency',
                        'https://github.com/LGE-OSS/fosslight_dependency', 'Copyright (c) 2020 LG Electronics, Inc.',
                        '', 'Awesome Open Source'],
                       ['askalono.exe', 'askalono',
                        '0.4.3', 'Apache-2.0',  'https://github.com/jpeddicord/askalono',
                        '', 'Copyright (c) 2018 Amazon.com, Inc. or its affiliates.',
                        '', '']]
    custom_tab_name = 'CUSTOM_HEADER_SHEET'
    sheet_items = [['ID', 'Binary Path', 'OSS Name', 'OSS Version',
                    'License', 'Download Location', 'Homepage',
                    'Copyright Text', 'Exclude', 'Comment'],
                   ['dependency_unified.py', 'fosslight_dependency',
                    '3.0.6', 'Apache-2.0',  'https://github.com/LGE-OSS/fosslight_dependency',
                    'https://github.com/LGE-OSS/fosslight_dependency', 'Copyright (c) 2020 LG Electronics, Inc.',
                    'Exclude', 'Awesome Open Source'],
                   ['askalono.exe', 'askalono',
                    '0.4.3', 'Apache-2.0',  'https://github.com/jpeddicord/askalono',
                    '', 'Copyright (c) 2018 Amazon.com, Inc. or its affiliates.',
                    '', '']]

    not_included_tab_name = 'SRC_NULL'

    sheet_contents[src_tab_name] = src_sheet_items
    sheet_contents[bin_tab_name] = bin_sheet_items
    sheet_contents[custom_tab_name] = sheet_items
    sheet_contents[not_included_tab_name] = []

    #when
    success, msg, result_file = write_output_file(file_to_create, file_extension, sheet_contents)

    #then
    assert success is True
    assert result_file_name + file_extension in result_file


