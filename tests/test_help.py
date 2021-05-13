#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util._help import PrintHelpMsgBase

_HELP_MESSAGE_TEST = """
    Usage Test [Test] <Test>

    Test Test Test
    """    
    

class PrintHelpMsg(PrintHelpMsgBase):
    def print_help_msg(self):
        super().print_help_msg()
        print(_HELP_MESSAGE_TEST)


helpMsg = PrintHelpMsg()


def main():
    helpMsg.print_help_msg()
 
if __name__ == '__main__':
    main()
