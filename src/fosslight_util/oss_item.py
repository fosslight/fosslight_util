#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from fosslight_util.constant import LOGGER_NAME, FL_DEPENDENCY, FL_BINARY
from typing import List
_logger = logging.getLogger(LOGGER_NAME)
 

class OssItem:

    def __init__(self, name, version, license, dl_url=""):
        self.name = name
        self.version = version
        self.license = license
        self.download_location = dl_url
        self.exclude = False
        self.comment = ""
        self.homepage = ""
        self._copyright = ""

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
    def exclude(self):
        return self._exclude

    @exclude.setter
    def exclude(self, value):
        if value:
            self._exclude = True
        else:
            self._exclude = False
    
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


class FileItem:
    def __init__(self, value):
        self.relative_path = value
        self.source_name_or_path = ""
        self._exclude = False
        self._comment = ""
        self.is_binary = False
        self.oss_items: List[OssItem] = []

    def __del__(self):
        pass

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

        for oss in self.oss_items:
            exclude = "Exclude" if self.exclude or oss.exclude else ""
            lic = ",".join(self.license)

            oss_item = [os.path.join(self.relative_path, self.source_name_or_path), oss.name, oss.version, oss.lic,
                        oss.download_location, oss.homepage, oss.copyright, exclude, oss.comment]
            items.append(oss_item)
        return items

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