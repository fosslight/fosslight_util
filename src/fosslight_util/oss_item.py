#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import hashlib
from fosslight_util.constant import LOGGER_NAME, FOSSLIGHT_SCANNER
from fosslight_util.cover import CoverItem
from typing import List, Dict

_logger = logging.getLogger(LOGGER_NAME)
CHECKSUM_NULL = "0"


class OssItem:

    def __init__(self, name="", version="", license="", dl_url=""):
        self.name = name
        self.version = version
        self._license = []
        self.license = license
        self.download_location = dl_url
        self.exclude = False
        self.comment = ""
        self.homepage = ""
        self._copyright = ""

    def __del__(self):
        pass

    @property
    def license(self):
        return self._license

    @license.setter
    def license(self, value):
        if value != "":
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


class FileItem:
    def __init__(self, value):
        self.relative_path = value
        self.source_name_or_path = ""
        self._exclude = False
        self._comment = ""
        self.is_binary = False
        self.oss_items: List[OssItem] = []
        self.checksum = CHECKSUM_NULL

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
        for oss in self.oss_items:
            oss.exclude = value

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
            for oss in self.oss_items:
                oss.comment = value

    def get_print_array(self):
        items = []

        for oss in self.oss_items:
            exclude = "Exclude" if self.exclude or oss.exclude else ""
            lic = ",".join(oss.license)

            oss_item = [os.path.join(self.relative_path, self.source_name_or_path), oss.name, oss.version, lic,
                        oss.download_location, oss.homepage, oss.copyright, exclude, oss.comment]
            items.append(oss_item)
        return items

    def get_print_json(self):
        items = []

        for oss in self.oss_items:
            json_item = {}
            json_item["name"] = oss.name
            json_item["version"] = oss.version

            if self.source_name_or_path != "":
                json_item["source path"] = self.source_name_or_path
            if len(oss.license) > 0:
                json_item["license"] = oss.license
            if oss.download_location != "":
                json_item["download location"] = oss.download_location
            if oss.homepage != "":
                json_item["homepage"] = oss.homepage
            if oss.copyright != "":
                json_item["copyright text"] = oss.copyright
            if self.exclude or oss.exclude:
                json_item["exclude"] = True
            if oss.comment != "":
                json_item["comment"] = oss.comment
            items.append(json_item)
        return items


def get_checksum_sha1(source_name_or_path) -> str:
    checksum = CHECKSUM_NULL
    try:
        checksum = str(hashlib.sha1(source_name_or_path.encode()).hexdigest())
    except Exception:
        try:
            f = open(source_name_or_path, "rb")
            byte = f.read()
            checksum = str(hashlib.sha1(byte).hexdigest())
            f.close()
        except Exception as ex:
            _logger.info(f"(Error) Get_checksum: {ex}")

    return checksum


def invalid(cmd):
    _logger.info('[{}] is invalid'.format(cmd))


class ScannerItem:
    def __init__(self, pkg_name, start_time=""):
        self.cover = CoverItem(tool_name=pkg_name, start_time=start_time)
        self.file_items: Dict[str, List[FileItem]] = {pkg_name: []} if pkg_name != FOSSLIGHT_SCANNER else {}
        self.external_sheets: Dict[str, List[List[str]]] = {}

    def set_cover_pathinfo(self, input_dir, path_to_exclude):
        self.cover.input_path = input_dir
        self.cover.exclude_path = ", ".join(path_to_exclude)

    def set_cover_comment(self, value):
        if value:
            if self.cover.comment:
                self.cover.comment = f"{self.cover.comment} / {value}"
            else:
                self.cover.comment = value

    def get_cover_comment(self):
        return [item.strip() for item in self.cover.comment.split(" / ")]

    def append_file_items(self, file_item: List[FileItem], pkg_name=""):
        if pkg_name == "":
            if len(self.file_items.keys()) != 1:
                _logger.error("Package name is not set. Cannot append file_item into ScannerItem.")
            else:
                pkg_name = list(self.file_items.keys())[0]
        if pkg_name not in self.file_items:
            self.file_items[pkg_name] = []
        self.file_items[pkg_name].extend(file_item)

    def get_print_array(self, scanner_name):
        items = []
        for file_item in self.file_items[scanner_name]:
            items.extend(file_item.get_print_array())
        return items

    def get_print_json(self, scanner_name):
        items = []
        for file_item in self.file_items[scanner_name]:
            items.extend(file_item.get_print_json())
        return items

    def __del__(self):
        pass
