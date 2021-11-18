#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import sys
from fosslight_util.output_format import write_output_file
from fosslight_util.set_log import init_log


def main():
    logger, _result_log = init_log("test_result/output_format/log_write_output.txt")

    sheet_list = {'SRC_FL_Source': [
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
                  ['test/askalono_macos', 'askalono', '', 'Apache-2.0', '', '', '', 'Exclude', '']],
                  'SRC_FL_Dependency': [
                  ['requirements.txt', 'pypi:future', '0.18.2', 'MIT', 'https://pypi.org/project/future/0.18.2',
                   'https://python-future.org', '', '', ''],
                  ['requirements.txt', 'pypi:numpy', '1.19.5', 'BSD-3-Clause-Open-MPI,GCC-exception-3.1,GPL-3.0',
                   'https://pypi.org/project/numpy/1.19.5', 'https://www.numpy.org', '', '', ''],
                  ['requirements.txt', 'pypi:pandas', '1.1.5', 'BSD-3-Clause', 'https://pypi.org/project/pandas/1.1.5',
                   'https://pandas.pydata.org', '', '', '']]}

    logger.warning("TESTING - Writing an excel output")
    success, msg = write_output_file(
        'test_result/output_format/FL-TEST_Excel', '.xlsx', sheet_list)
    logger.warning("Result:" + str(success) + ", error_msg:" + msg)

    if not success:
        sys.exit(1)

    logger.warning("TESTING - Writing an opossum output")
    success, msg = write_output_file(
        'test_result/output_format/FL-TEST_opossum', '.json', sheet_list)
    logger.warning("Result:" + str(success) + ", error_msg:" + msg)

    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
