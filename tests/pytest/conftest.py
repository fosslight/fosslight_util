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
