#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.help import PrintHelpMsg, print_package_version


def main():
    _HELP_MESSAGE_TEST = """
        Usage Test [Test] <Test>

        Test Test Test
    """
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_TEST)
    helpMsg.print_help_msg(False)

    print_package_version("fosslight_util", "FOSSLight Util Version")


if __name__ == '__main__':
    main()
