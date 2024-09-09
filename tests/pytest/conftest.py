import pytest
import os
import shutil

set_up_directories = ["test_result", "test_result/convert"]
remove_directories = ["test_result"]

@pytest.fixture(scope="function", autouse=True)
def setup_test_result_dir_and_teardown():
    print("==============setup==============")

    for dir in set_up_directories:
        os.makedirs(dir, exist_ok=True)

    yield

    print("==============tearDown==============")
    for dir in remove_directories:
        shutil.rmtree(dir)


@pytest.fixture
def sheet_list_fixture():
    sheet_contents = {}
    include_tab_name = []

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

    include_tab_name.append(src_tab_name)
    include_tab_name.append(bin_tab_name)
    include_tab_name.append(custom_tab_name)

    sheet_contents[src_tab_name] = src_sheet_items
    sheet_contents[bin_tab_name] = bin_sheet_items
    sheet_contents[custom_tab_name] = sheet_items

    return include_tab_name, sheet_contents
