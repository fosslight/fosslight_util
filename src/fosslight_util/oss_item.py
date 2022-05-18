#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
from fosslight_util.constant import LOGGER_NAME

_logger = logging.getLogger(LOGGER_NAME)


class OssItem:
    def __init__(self, value):
        self._name = "-"
        self._version = ""
        self._licenses = []
        self._copyright = ""
        self.comment = ""
        self._exclude = False
        self.homepage = ""
        self.relative_path = value
        self._source_name_or_path = []
        self.download_location = ""

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
    def licenses(self):
        return self._licenses

    @licenses.setter
    def licenses(self, value):
        if not isinstance(value, list):
            value = value.split(",")
        self._licenses.extend(value)
        self._licenses = [item.strip() for item in self._licenses]
        self._licenses = list(set(self._licenses))

    @property
    def source_name_or_path(self):
        return self._source_name_or_path

    @source_name_or_path.setter
    def source_name_or_path(self, value):
        if isinstance(value, list):
            self._source_name_or_path.extend(value)
        else:
            self._source_name_or_path.append(value)
        self._source_name_or_path = list(set(self._source_name_or_path))

    def set_sheet_item(self, item):
        if len(item) < 9:
            _logger.warning(f"sheet list is too short ({len(item)}): {item}")
            return
        self.source_name_or_path = item[0]
        self.name = item[1]
        self.version = item[2]
        self.licenses = item[3]
        self.download_location = item[4]
        self.homepage = item[5]
        self.copyright = item[6]
        self.exclude = item[7]
        self.comment = item[8]

    def get_print_array(self):
        items = []
        if len(self.source_name_or_path) == 0:
            self.source_name_or_path.append("")
        if len(self.licenses) == 0:
            self.licenses.append("")

        exclude = "Exclude" if self.exclude else ""

        for source_name_or_path in self.source_name_or_path:
            lic = ",".join(self.licenses)
            if self.relative_path != "" and not str(self.relative_path).endswith("/"):
                self.relative_path += "/"
            items.append([self.relative_path + source_name_or_path, self.name, self.version, lic,
                          self.download_location, self.homepage, self.copyright, "", exclude, self.comment])
        return items

    def get_print_json(self):
        json_item = {}
        json_item["name"] = self.name

        json_item["version"] = self.version
        if len(self.source_name_or_path) > 0:
            json_item["source_name_or_path"] = self.source_name_or_path
        if len(self.licenses) > 0:
            json_item["license"] = self.licenses
        if self.download_location != "":
            json_item["download_location"] = self.download_location
        if self.homepage != "":
            json_item["homepage"] = self.homepage
        if self.copyright != "":
            json_item["copyright_text"] = self.copyright
        if self.exclude:
            json_item["exclude"] = self.exclude
        if self.comment != "":
            json_item["comment"] = self.comment

        return json_item


def invalid(cmd):
    _logger.info('[{}] is invalid'.format(cmd))
