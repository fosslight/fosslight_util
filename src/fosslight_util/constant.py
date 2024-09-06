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
                               f'BIN_{FL_BINARY}': FL_BINARY,
                               f'DEP_{FL_DEPENDENCY}': FL_DEPENDENCY}

FOSSLIGHT_SCANNER = 'fosslight_scanner'
FOSSLIGHT_SOURCE = 'fosslight_source'
FOSSLIGHT_DEPENDENCY = 'fosslight_dependency'
FOSSLIGHT_BINARY = 'fosslight_binary'

SHEET_NAME_FOR_SCANNER = {
    FOSSLIGHT_SOURCE: 'SRC_FL_Source',
    FOSSLIGHT_BINARY: 'BIN_FL_Binary',
    FOSSLIGHT_DEPENDENCY: 'DEP_FL_Dependency'
}

# Github : https://github.com/(owner)/(repo)
# npm : https://www.npmjs.com/package/(package)/v/(version)
# npm2 : https://www.npmjs.com/package/@(group)/(package)/v/(version)
# pypi : https://pypi.org/project/(oss_name)/(version)
# pypi2 : https://files.pythonhosted.org/packages/source/(alphabet)/(oss_name)/(oss_name)-(version).tar.gz
# Maven: https://mvnrepository.com/artifact/(group)/(artifact)/(version)
# pub: https://pub.dev/packages/(package)/versions/(version)
# Cocoapods : https://cocoapods.org/(package)
# go : https://pkg.go.dev/(package_name_with_slash)@(version)
PKG_PATTERN = {
    "pypi": r'https?:\/\/pypi\.org\/project\/([^\/]+)[\/]?([^\/]*)',
    "pypi2": r'https?:\/\/files\.pythonhosted\.org\/packages\/source\/[\w]\/([^\/]+)\/[\S]+-([^\-]+)\.tar\.gz',
    "maven": r'https?:\/\/mvnrepository\.com\/artifact\/([^\/]+)\/([^\/]+)\/?([^\/]*)',
    "npm": r'https?:\/\/www\.npmjs\.com\/package\/([^\/\@]+)(?:\/v\/)?([^\/]*)',
    "npm2": r'https?:\/\/www\.npmjs\.com\/package\/(\@[^\/]+\/[^\/]+)(?:\/v\/)?([^\/]*)',
    "pub": r'https?:\/\/pub\.dev\/packages\/([^\/]+)(?:\/versions\/)?([^\/]*)',
    "cocoapods": r'https?:\/\/cocoapods\.org\/pods\/([^\/]+)',
    "go": r'https?:\/\/pkg.go.dev\/([^\@]+)\@?v?([^\/]*)'
}
