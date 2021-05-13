#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: LicenseRef-LGE-Proprietary
_HELP_MESSAGE_COMMON = """
     _______  _______  _______  _______  ___      ___   _______  __   __  _______ 
    |       ||       ||       ||       ||   |    |   | |       ||  | |  ||       |
    |    ___||   _   ||  _____||  _____||   |    |   | |    ___||  |_|  ||_     _|
    |   |___ |  | |  || |_____ | |_____ |   |    |   | |   | __ |       |  |   |  
    |    ___||  |_|  ||_____  ||_____  ||   |___ |   | |   ||  ||   _   |  |   |  
    |   |    |       | _____| | _____| ||       ||   | |   |_| ||  | |  |  |   |  
    |___|    |_______||_______||_______||_______||___| |_______||__| |__|  |___|  
"""
from abc import *

class PrintHelpMsgBase(metaclass=ABCMeta):
    @abstractmethod
    def print_help_msg(self):
        print(_HELP_MESSAGE_COMMON)