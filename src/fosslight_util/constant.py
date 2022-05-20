#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

LOGGER_NAME = "FOSSLight"

FL_SOURCE = 'FL_Source'
FL_DEPENDENCY = 'FL_Dependency'
FL_BINARY = 'FL_Binary'
supported_sheet_and_scanner = {'SRC': FL_SOURCE,
                               'BIN': FL_BINARY,
                               f'SRC_{FL_SOURCE}': FL_SOURCE,
                               f'SRC_{FL_DEPENDENCY}': FL_DEPENDENCY,
                               f'BIN_{FL_BINARY}': FL_BINARY}
