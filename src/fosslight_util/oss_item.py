#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from fosslight_util.constant import LOGGER_NAME, FL_DEPENDENCY, FL_BINARY

_logger = logging.getLogger(LOGGER_NAME)


class OssItem:
    def __init__(self, value):
        self._name = ""
        self._version = ""
        self._license = []
        self._copyright = ""
        self.comment = ""
        self._exclude = False
        self.homepage = ""
        self.relative_path = value
        self._source_name_or_path = []
        self.download_location = ""
        self._yocto_recipe = []
        self._yocto_package = []
        self.is_binary = False
        self._depends_on = []
        self.purl = ""
        self.bin_vulnerability = ""
        self.bin_tlsh = ""
        self.bin_sha1 = ""

    def __del__(self):
        pass

    @property
    def copyright(self):
        return self._copyright

    @copyright.setter
    def copyright(self, value):
        if value != "":
            if isinstance(value, list):
                value = "\n".join(value)
            value = value.strip()
        self._copyright = value

    @property
    def exclude(self):
        return self._exclude

    @exclude.setter
    def exclude(self, value):
        if value:
            self._exclude = True
        else:
            self._exclude = False

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value != "":
            self._name = value

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        if value:
            self._version = str(value)
        else:
            self._version = ""

    @property
    def license(self):
        return self._license

    @license.setter
    def license(self, value):
        if not isinstance(value, list):
            value = value.split(",")
        self._license.extend(value)
        self._license = [item.strip() for item in self._license]
        self._license = list(set(self._license))

    @property
    def source_name_or_path(self):
        return self._source_name_or_path

    @source_name_or_path.setter
    def source_name_or_path(self, value):
        if not value:
            self._source_name_or_path = []
        else:
            if not isinstance(value, list):
                value = value.split(",")
            self._source_name_or_path.extend(value)
            self._source_name_or_path = [item.strip() for item in self._source_name_or_path]
            self._source_name_or_path = list(set(self._source_name_or_path))

    @property
    def yocto_recipe(self):
        return self._yocto_recipe

    @yocto_recipe.setter
    def yocto_recipe(self, value):
        if not isinstance(value, list):
            value = value.split(",")
        self._yocto_recipe.extend(value)
        self._yocto_recipe = [item.strip() for item in self._yocto_recipe]
        self._yocto_recipe = list(set(self._yocto_recipe))

    @property
    def yocto_package(self):
        return self._yocto_package

    @yocto_package.setter
    def yocto_package(self, value):
        if not isinstance(value, list):
            value = value.split(",")
        self._yocto_package.extend(value)
        self._yocto_package = [item.strip() for item in self._yocto_package]
        self._yocto_package = list(set(self._yocto_package))

    @property
    def depends_on(self):
        return self._depends_on

    @depends_on.setter
    def depends_on(self, value):
        if not value:
            self._depends_on = []
        else:
            if not isinstance(value, list):
                value = value.split(",")
            self._depends_on.extend(value)
            self._depends_on = [item.strip() for item in self._depends_on]
            self._depends_on = list(set(self._depends_on))

    def set_sheet_item(self, item, scanner_name=''):
        if len(item) < 9:
            _logger.warning(f"sheet list is too short ({len(item)}): {item}")
            return
        if scanner_name == FL_DEPENDENCY:
            self.purl = item[0]
        else:
            self.source_name_or_path = item[0]
        self.name = item[1]
        self.version = item[2]
        self.license = item[3]
        self.download_location = item[4]
        self.homepage = item[5]
        self.copyright = item[6]
        self.exclude = item[7]
        self.comment = item[8]

        if len(item) >= 10 and scanner_name == FL_DEPENDENCY:
            self.depends_on = item[9]
        if len(item) >= 10 and scanner_name == FL_BINARY:
            self.bin_vulnerability = item[9]
            if len(item) >= 12:
                self.bin_tlsh = item[10]
                self.bin_sha1 = item[11]

    def get_print_array(self, scanner_name=''):
        items = []
        if scanner_name != FL_DEPENDENCY:
            if len(self.source_name_or_path) == 0:
                self.source_name_or_path.append("")
        if len(self.license) == 0:
            self.license.append("")

        exclude = "Exclude" if self.exclude else ""
        lic = ",".join(self.license)
        if scanner_name == FL_DEPENDENCY:
            items = [self.purl, self.name, self.version, lic,
                     self.download_location, self.homepage, self.copyright, exclude, self.comment]
            if len(self.depends_on) > 0:
                items.append(",".join(self.depends_on))
        else:
            for source_name_or_path in self.source_name_or_path:
                if scanner_name == FL_BINARY:
                    oss_item = [os.path.join(self.relative_path, source_name_or_path), self.name, self.version, lic,
                                self.download_location, self.homepage, self.copyright, exclude, self.comment,
                                self.bin_vulnerability, self.bin_tlsh, self.bin_sha1]
                else:
                    oss_item = [os.path.join(self.relative_path, source_name_or_path), self.name, self.version, lic,
                                self.download_location, self.homepage, self.copyright, exclude, self.comment]
                items.append(oss_item)
        return items

    def get_print_json(self):
        json_item = {}
        json_item["name"] = self.name

        json_item["version"] = self.version
        if len(self.source_name_or_path) > 0:
            json_item["source name or path"] = self.source_name_or_path
        if len(self.license) > 0:
            json_item["license"] = self.license
        if self.download_location != "":
            json_item["download location"] = self.download_location
        if self.homepage != "":
            json_item["homepage"] = self.homepage
        if self.copyright != "":
            json_item["copyright text"] = self.copyright
        if self.exclude:
            json_item["exclude"] = self.exclude
        if self.comment != "":
            json_item["comment"] = self.comment
        if len(self.depends_on) > 0:
            json_item["depends on"] = self.depends_on
        if self.purl != "":
            json_item["purl"] = self.purl

        return json_item


def invalid(cmd):
    _logger.info('[{}] is invalid'.format(cmd))
