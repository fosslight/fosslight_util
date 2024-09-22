# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import shutil

import pytest

from . import constants

set_up_directories = [
    constants.TEST_RESULT_DIR,
    os.path.join(constants.TEST_RESULT_DIR, "convert")
]
remove_directories = [constants.TEST_RESULT_DIR]


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


@pytest.fixture
def sheet_list_fixture_for_write_yaml():
    sheet_list = {'SRC_FL_Source': [
        ['test/lib/not_license.js', '', '', '', '', '',
         'Copyright (c) 2014, Facebook, Inc.', 'Exclude', ''],
        ['test/lib/babel-polyfill.js', '', '', 'bsd-3-clause,facebook-patent-rights-2', '', '',
         'Copyright (c) 2014, Facebook, Inc.', 'Exclude', ''],
        ['test/lib/babel-polyfill2.js', '', '', 'bsd-3-clause,facebook-patent-rights-2', '', '',
         'Copyright (c) 2014, Facebook, Inc.', 'Exclude', 'test_commend'],
        ['test/lib/babel-polyfill.js', '', '', 'bsd-3-clause,facebook-patent-rights-2', '', '',
         'Copyright (c) 2014, Facebook, Inc.', 'Exclude', ''],
        ['lib/babel-polyfill.js', '', '', 'bsd-3-clause', '', '',
         'Copyright (c) 2014, Facebook, Inc.', '', ''],
        ['lib/babel-polyfill.js', '', '', 'facebook-patent-rights-2', '', '',
         'Copyright (c) 2014, Facebook, Inc.', '', ''],
        ['requirements.txt', '', '', 'MIT', 'https://pypi.org/project/future/0.18.2', '', '', '', ''],
        ['bower.json', '', '', 'mit', '', '', '', '', ''],
        ['LICENSE', '', '', 'mit', '', '', 'Copyright (c) 2016-2021, The Cytoscape Consortium', '', ''],
        ['license-update.js', '', '', 'mit', '', '', 'Copyright (c) 2016-$ year, The Cytoscape Consortium', '', ''],
        ['package.json', '', '', 'mit', '', '', '', '', ''], ['README.md', '', '', 'mit', '', '', '', '', ''],
        ['dist/cytoscape.cjs.js', '', '', 'mit', '', '', 'Copyright Gaetan Renaudeau,Copyright (c) 2016-2021,c \
                   The Cytoscape Consortium,copyright Koen Bok,Copyright (c) 2013-2014 Ralf S. Engelschall \
                   (http://engelschall.com)', '', ''],
        ['dist/cytoscape.esm.js', '', '', 'mit', '', '', 'Copyright Gaetan Renaudeau,Copyright (c) 2016-2021,\
                   The Cytoscape Consortium,copyright Koen Bok,Copyright (c) 2013-2014 Ralf S. Engelschall \
                   (http://engelschall.com)', '', ''],
        ['dist/cytoscape.esm.min.js', '', '', 'mit', '', '', 'Copyright Gaetan Renaudeau,copyright Koen Bok, \
                   Copyright (c) 2013-2014 Ralf S. Engelschall (http://engelschall.com)', '', ''],
        ['dist/cytoscape.min.js', '', '', 'mit',
         '', '', 'Copyright Gaetan Renaudeau,Copyright (c) 2016-2021, The Cytoscape Consortium,copyright Koen Bok,Copyright \
                  (c) 2013-2014 Ralf S. Engelschall (http://engelschall.com)', '', ''],
        ['dist/cytoscape.umd.js', '', '', 'mit', '', '',
         'Copyright Jeremy Ashkenas, DocumentCloud and Investigative Reporters & Editors,Copyright jQuery Foundation \
         and other contributors <https://jquery.org/>,Copyright (c) 2016-2021, The Cytoscape Consortium,copyright Koen\
         Bok,Copyright Gaetan Renaudeau,Copyright (c) 2013-2014 Ralf S. Engelschall (http://engelschall.com)', '', ''],
        ['documentation/css/highlight/monokai_sublime.css', '', '', 'mit', '', '', '', '', ''],
        ['documentation/js/cytoscape.min.js', '', '', 'mit', '', '', 'Copyright Gaetan Renaudeau,\
                   Copyright (c) 2016-2021, The Cytoscape Consortium,copyright Koen Bok, \
                   Copyright (c) 2013-2014 Ralf S. Engelschall (http://engelschall.com)', '', ''],
        ['documentation/md/links.md', '', '', 'mit', '', '', '', '', ''],
        ['src/event.js', '', '', 'mit', '', '', '', '', '']],
        'BIN_FL_Binary': [
            ['askalono_macos', 'askalono', '', 'Apache-2.0', '', '', '', '', ''],
            ['test/askalono_macos', 'askalono', '', 'Apache-2.0', '', '', '', 'Exclude', '']],
        'SRC_FL_Dependency': [
            ['requirements.txt', 'pypi:future', '0.18.2', 'MIT', 'https://pypi.org/project/future/0.18.2',
             'https://python-future.org', '', '', ''],
            ['requirements.txt', 'pypi:numpy', '1.19.5', 'BSD-3-Clause-Open-MPI,GCC-exception-3.1,GPL-3.0',
             'https://pypi.org/project/numpy/1.19.5', 'https://www.numpy.org', '', '', ''],
            ['requirements.txt', 'pypi:pandas', '1.1.5', 'BSD-3-Clause', 'https://pypi.org/project/pandas/1.1.5',
             'https://pandas.pydata.org', '', '', '']]}

    sheet_list2 = {'SRC_FL_Dependency': [
        ['requirements.txt', 'pypi:future', '0.18.2', 'MIT', 'https://pypi.org/project/future/0.18.2',
            'https://python-future.org', '', '', ''],
        ['requirements.txt', 'pypi:numpy', '1.19.5', 'BSD-3-Clause-Open-MPI,GCC-exception-3.1,GPL-3.0',
         'https://pypi.org/project/numpy/1.19.5', 'https://www.numpy.org', '', '', ''],
        ['requirements.txt', 'pypi:pandas', '1.1.5', 'BSD-3-Clause', 'https://pypi.org/project/pandas/1.1.5',
         'https://pandas.pydata.org', '', '', '']],
        'SRC_FL_Source': [
            ['test/lib/babel-polyfill.js', '', '', 'bsd-3-clause,facebook-patent-rights-2', '', '',
             'Copyright (c) 2014, Facebook, Inc.', 'Exclude', ''],
            ['requirements.txt', '', '', 'MIT', 'https://pypi.org/project/future/0.18.2', '', '', '', ''],
            ['bower.json', '', '', 'mit', '', '', '', '', ''],
            ['LICENSE', '', '', 'mit', '', '', 'Copyright (c) 2016-2021, The Cytoscape Consortium', '', ''],
            ['license-update.js', '', '', 'mit', '', '', 'Copyright (c) 2016-$ year, The Cytoscape Consortium', '', ''],
            ['package.json', '', '', 'mit', '', '', '', '', ''], ['README.md', '', '', 'mit', '', '', '', '', ''],
            ['dist/cytoscape.cjs.js', '', '', 'mit', '', '', 'Copyright Gaetan Renaudeau,Copyright (c) 2016-2021,c \
                       The Cytoscape Consortium,copyright Koen Bok,Copyright (c) 2013-2014 Ralf S. Engelschall \
                       (http://engelschall.com)', '', ''],
            ['dist/cytoscape.esm.js', '', '', 'mit', '', '', 'Copyright Gaetan Renaudeau,Copyright (c) 2016-2021,\
                       The Cytoscape Consortium,copyright Koen Bok,Copyright (c) 2013-2014 Ralf S. Engelschall \
                       (http://engelschall.com)', '', ''],
            ['dist/cytoscape.esm.min.js', '', '', 'mit', '', '', 'Copyright Gaetan Renaudeau,copyright Koen Bok, \
                       Copyright (c) 2013-2014 Ralf S. Engelschall (http://engelschall.com)', '', ''],
            ['dist/cytoscape.min.js', '', '', 'mit',
             '', '', 'Copyright Gaetan Renaudeau,Copyright (c) 2016-2021, The Cytoscape Consortium,copyright Koen Bok,Copyright \
                      (c) 2013-2014 Ralf S. Engelschall (http://engelschall.com)', '', ''],
            ['dist/cytoscape.umd.js', '', '', 'mit', '', '',
             'Copyright Jeremy Ashkenas, DocumentCloud and Investigative Reporters & Editors,Copyright jQuery Foundation \
             and other contributors <https://jquery.org/>,Copyright (c) 2016-2021, The Cytoscape Consortium,copyright Koen\
             Bok,Copyright Gaetan Renaudeau,Copyright (c) 2013-2014 Ralf S. Engelschall (http://engelschall.com)', '', ''],
            ['documentation/css/highlight/monokai_sublime.css', '', '', 'mit', '', '', '', '', ''],
            ['documentation/js/cytoscape.min.js', '', '', 'mit', '', '', 'Copyright Gaetan Renaudeau,\
                       Copyright (c) 2016-2021, The Cytoscape Consortium,copyright Koen Bok, \
                       Copyright (c) 2013-2014 Ralf S. Engelschall (http://engelschall.com)', '', ''],
            ['documentation/md/links.md', '', '', 'mit', '', '', '', '', ''],
            ['src/event.js', '', '', 'mit', '', '', '', '', '']],
        'BIN_FL_Binary': [
            ['askalono_macos', 'askalono', '', 'Apache-2.0', '', '', '', '', ''],
            ['test/askalono_macos', 'askalono', '', 'Apache-2.0', '', '', '', 'Exclude', '']]}

    return sheet_list, sheet_list2
