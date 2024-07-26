#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from fosslight_util.constant import LOGGER_NAME

_logger = logging.getLogger(LOGGER_NAME)


class OssItem:
    def __init__(self, value):
        self.relative_path = value

        self._source_name_or_path = []
        self._name = ""
        self._version = ""
        self._license = []
        self.download_location = ""
        self.homepage = ""
        self._copyright = ""
        self._exclude = False
        self._comment = ""

        self.is_binary = False

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
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, value):
        if not value:
            self._comment = ""
        else:
            if self._comment:
                self._comment = f"{self._comment} / {value}"
            else:
                self._comment = value

    def get_print_array(self):
        items = []

        if len(self.source_name_or_path) == 0:
            self.source_name_or_path.append("")
        if len(self.license) == 0:
            self.license.append("")

        exclude = "Exclude" if self.exclude else ""
        lic = ",".join(self.license)

        for source_name_or_path in self.source_name_or_path:
            oss_item = [os.path.join(self.relative_path, source_name_or_path), self.name, self.version, lic,
                        self.download_location, self.homepage, self.copyright, exclude, self.comment]
            items.append(oss_item)
        return items

    '''
    def get_print_array(self): # 나중에 BinaryItem용 함수로 옮겨야 함
        items = []

        if len(self.source_name_or_path) == 0:
            self.source_name_or_path.append("")
        if len(self.license) == 0:
            self.license.append("")

        exclude = "Exclude" if self.exclude else ""
        lic = ",".join(self.license)

        for source_name_or_path in self.source_name_or_path:
            oss_item = [os.path.join(self.relative_path, source_name_or_path), self.name, self.version, lic,
                        self.download_location, self.homepage, self.copyright, exclude, self.comment,
                        self.bin_vulnerability, self.bin_tlsh, self.bin_sha1]
            items.append(oss_item)
        return items
    '''
    def get_print_json(self):
        json_item = {}
        json_item["name"] = self.name

        json_item["version"] = self.version
        if len(self.source_name_or_path) > 0:
            json_item["source path"] = self.source_name_or_path
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

        return json_item


def invalid(cmd):
    _logger.info('[{}] is invalid'.format(cmd))
