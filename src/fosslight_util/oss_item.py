#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
from fosslight_util.constant import LOGGER_NAME

_logger = logging.getLogger(LOGGER_NAME)


class OssItem:
    name = "-"
    version = ""
    licenses = []
    source = ""
    files = []
    copyright = ""
    comment = ""
    exclude = ""
    homepage = ""
    relative_path = ""
    source_name_or_path = []
    download_location = ""
    copyright_text = ""

    def __init__(self, value):
        self.name = "-"
        self.version = ""
        self.licenses = []
        self.source = ""
        self.files = []
        self.copyright = ""
        self.comment = ""
        self.exclude = ""
        self.homepage = ""
        self.relative_path = value
        self.source_name_or_path = []
        self.download_location = ""
        self.copyright_text = ""

    def __del__(self):
        pass

    def set_homepage(self, value):
        self.homepage = value

    def set_comment(self, value):
        self.comment = value

    def set_copyright(self, value):
        if value != "":
            if isinstance(value, list):
                value = "\n".join(value)
            value = value.strip()
        self.copyright = value

    def set_exclude(self, value):
        if value:
            self.exclude = True
        else:
            self.exclude = False

    def set_name(self, value):
        if value != "":
            self.name = value

    def set_version(self, value):
        if value:
            self.version = str(value)
        else:
            self.version = ""

    def set_licenses(self, value):
        if not isinstance(value, list):
            value = value.split(",")
        self.licenses.extend(value)
        self.licenses = [item.strip() for item in self.licenses]
        self.licenses = list(set(self.licenses))

    def set_files(self, value):
        if isinstance(value, list):
            self.files.extend(value)
        else:
            self.files.append(value)
        self.files = list(set(self.files))

    def set_source(self, value):
        self.source = value

    # new keys for updated yaml format
    # replace 'file' key
    def set_source_name_or_path(self, value):
        if not isinstance(value, list):
            value = value.split(",")
        self.source_name_or_path.extend(value)
        self.source_name_or_path = [item.strip() for item in self.source_name_or_path]
        self.source_name_or_path = list(set(self.source_name_or_path))

    # replace 'source' key
    def set_download_location(self, value):
        self.download_location = value

    # replace 'copyright' key
    def set_copyright_text(self, value):
        self.copyright_text = value

    def set_sheet_item(self, item):
        switcher = {
            0: self.set_source_name_or_path,
            1: self.set_name,
            2: self.set_version,
            3: self.set_licenses,
            4: self.set_download_location,
            5: self.set_homepage,
            6: self.set_copyright_text,
            7: self.set_exclude,
            8: self.set_comment
        }

        for i in range(0, len(switcher)):
            func = switcher.get(i, "invalid")
            func(item[i])

    def get_print_array(self):
        items = []
        if len(self.files) == 0:
            self.files.append("")
        if len(self.licenses) == 0:
            self.licenses.append("")

        exclude = ""
        if self.exclude:
            exclude = "Exclude"

        for file in self.files:
            lic = ",".join(self.licenses)
            if self.relative_path != "" and not str(self.relative_path).endswith("/"):
                self.relative_path += "/"
            items.append([self.relative_path + file, self.name, self.version, lic, self.source, self.homepage,
                          self.copyright, "", exclude, self.comment])
        return items

    def get_print_json(self):
        json_item = {}
        json_item["name"] = self.name

        json_item["version"] = self.version
        if len(self.files) > 0:
            json_item["file"] = self.files
        if len(self.source_name_or_path) > 0:
            json_item["source_name_or_path"] = self.source_name_or_path
        if len(self.licenses) > 0:
            json_item["license"] = self.licenses
        if self.source != "":
            json_item["source"] = self.source
        if self.download_location != "":
            json_item["download_location"] = self.download_location
        if self.homepage != "":
            json_item["homepage"] = self.homepage
        if self.copyright != "":
            json_item["copyright"] = self.copyright
        if self.copyright_text != "":
            json_item["copyright_text"] = self.copyright_text
        if self.exclude:
            json_item["exclude"] = self.exclude
        if self.comment != "":
            json_item["comment"] = self.comment

        return json_item


def invalid(cmd):
    _logger.info('[{}] is invalid'.format(cmd))
