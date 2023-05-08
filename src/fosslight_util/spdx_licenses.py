#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

from urllib.request import urlopen
import os
import sys
import json
import traceback

_resources_dir = 'resources'
_licenses_json_file = 'licenses.json'
_frequentLicenselist_file = 'frequentLicenselist.json'
_frequent_lic_nick_json_file = 'frequent_license_nick_list.json'


def get_license_from_nick():
    licenses = {}
    licenses_file = os.path.join(_resources_dir, _frequent_lic_nick_json_file)

    try:
        base_dir = os.path.join(sys._MEIPASS, vars(sys.modules[__name__])['__package__'])
    except Exception:
        base_dir = os.path.dirname(__file__)

    file_withpath = os.path.join(base_dir, licenses_file)
    try:
        with open(file_withpath, 'r') as f:
            licenses = json.load(f)
    except Exception as ex:
        print(f"Error to get license from json file : {ex}")

    return licenses


def get_spdx_licenses_json():
    success = True
    error_msg = ''
    licenses = ''
    # licenses : https://github.com/spdx/license-list-data/blob/v3.17/json/licenses.json
    licenses_file = os.path.join(_resources_dir, _licenses_json_file)

    try:
        base_dir = os.path.join(sys._MEIPASS, vars(sys.modules[__name__])['__package__'])
    except Exception:
        base_dir = os.path.dirname(__file__)

    file_withpath = os.path.join(base_dir, licenses_file)
    try:
        with open(file_withpath, 'r') as f:
            licenses = json.load(f)
    except Exception as e:
        success = False
        error_msg = 'Failed to open ' + file_withpath + ': ' + str(e)

    return success, error_msg, licenses


def create_frequentlicenses():
    success = True
    error_msg = ''
    licenses = ''
    frequentLicenses = {}
    _frequentLicenses_key = 'frequentLicenses'

    # spdx_txt_url = _spdx_txt_base_url + version + /text/ + licenseId + '.txt'
    _spdx_txt_base_url = 'https://raw.githubusercontent.com/spdx/license-list-data/'

    try:
        success, error_msg, licenses = get_spdx_licenses_json()
        if success:
            version = licenses['licenseListVersion']
            frequentLicenses[_frequentLicenses_key] = []
            for lic in licenses['licenses']:
                tmp_lic = {}
                tmp_lic["fullName"] = lic['name']
                tmp_lic["shortName"] = lic['licenseId']

                deprecated = lic['isDeprecatedLicenseId']
                if deprecated:
                    spdx_txt_url = _spdx_txt_base_url + 'v' + version + '/text/' + 'deprecated_' + lic['licenseId'] + '.txt'
                else:
                    spdx_txt_url = _spdx_txt_base_url + 'v' + version + '/text/' + lic['licenseId'] + '.txt'

                with urlopen(spdx_txt_url) as url:
                    licenseText = url.read().decode('utf-8')
                tmp_lic["defaultText"] = licenseText

                frequentLicenses[_frequentLicenses_key].append(tmp_lic)

    except Exception as e:
        success = False
        error_msg = 'Failed to open and parse licenses.json'
        print(error_msg, ": ", e)
        print(traceback.format_exc())

    return frequentLicenses, success, error_msg


def main():
    _frequencyLicense = os.path.join(_resources_dir, _frequentLicenselist_file)
    frequentLicenses, success, error_msg = create_frequentlicenses()
    if success:
        with open(_frequencyLicense, 'w', encoding='utf-8') as f:
            json.dump(frequentLicenses, f, sort_keys=True, indent=4)
        print("Created " + _frequentLicenselist_file + " in " + _resources_dir)


if __name__ == '__main__':
    main()
