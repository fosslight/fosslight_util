#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import urllib.request
from urllib.error import URLError, HTTPError
from defusedxml.ElementTree import fromstring as xml_fromstring
import ssl
# certifi is optional: if unavailable, use the default SSL context
try:
    import certifi  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    certifi = None
import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)


def get_license_from_pom(group_id: str = None,
                         artifact_id: str = None,
                         version: str = None,
                         pom_path: str = None,
                         check_parent: bool = True) -> str:

    def get_ssl_context():
        try:
            if certifi is not None:
                return ssl.create_default_context(cafile=certifi.where())
            return ssl.create_default_context()
        except Exception as e:
            logger.debug(f"Failed to create SSL context: {e}")
            return None

    def build_urls(g, a, v):
        group_path = g.replace('.', '/')
        name = f"{a}-{v}.pom"
        repo1 = f"https://repo1.maven.org/maven2/{group_path}/{a}/{v}/{name}"
        google = f"https://dl.google.com/android/maven2/{group_path}/{a}/{v}/{name}"
        return [repo1, google]

    def fetch_pom(g, a, v):
        ssl_ctx = get_ssl_context()
        for url in build_urls(g, a, v):
            try:
                if ssl_ctx is not None:
                    with urllib.request.urlopen(url, context=ssl_ctx) as resp:
                        return resp.read().decode('utf-8')
                with urllib.request.urlopen(url) as resp:
                    return resp.read().decode('utf-8')
            except ssl.SSLError as e:
                logger.warning(
                    f"SSL certificate verification failed for {url}. "
                    f"Please fix system certificates or use certifi. (error: {e})"
                )
                continue
            except (HTTPError, URLError) as e:
                logger.warning(f"Failed to fetch POM from {url}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error fetching POM from {url}: {e}")
                continue
        return None

    def extract_licenses(root):
        licenses_elem = root.find('{*}licenses')
        if licenses_elem is not None:
            names = []
            for lic in licenses_elem.findall('{*}license'):
                name = lic.findtext('{*}name')
                if name:
                    names.append(name.replace(',', ''))
            if names:
                return ', '.join(names)
        return None

    def extract_parent_info(root):
        parent = root.find('{*}parent')
        if parent is not None:
            g = parent.findtext('{*}groupId') or parent.findtext('groupId')
            a = parent.findtext('{*}artifactId') or parent.findtext('artifactId')
            v = parent.findtext('{*}version') or parent.findtext('version')
            if g and a and v:
                return g, a, v
        return None, None, None

    visited = set()

    def find_license_in_pom_recursive(g, a, v, check_parent_flag):
        key = (g, a, v)
        if key in visited:
            return ''
        visited.add(key)
        content = fetch_pom(g, a, v)
        if not content:
            logger.warning(f"Failed to obtain POM content for {g}:{a}:{v} from remote sources.")
            return ''
        try:
            root = xml_fromstring(content)
        except Exception as e:
            logger.warning(f"Failed to parse POM for {g}:{a}:{v}: {e}")
            return ''
        licenses = extract_licenses(root)
        if licenses:
            return licenses
        if not check_parent_flag:
            return ''
        pg, pa, pv = extract_parent_info(root)
        if pg and pa and pv:
            return find_license_in_pom_recursive(pg, pa, pv, check_parent_flag)
        return ''

    try:
        if pom_path:
            if not os.path.exists(pom_path):
                logger.warning(f"POM file not found: {pom_path}")
                return ''
            try:
                with open(pom_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                xml_start = content.find('<?xml')
                if xml_start > 0:
                    content = content[xml_start:]
                elif xml_start == -1:
                    root_start = content.find('<project')
                    if root_start > 0:
                        content = content[root_start:]
                root = xml_fromstring(content)
            except Exception as e:
                logger.warning(f"Failed to parse POM file {pom_path}: {e}")
                return ''

            licenses = extract_licenses(root)
            if licenses:
                return licenses
            if not check_parent:
                return ''
            pg, pa, pv = extract_parent_info(root)
            if pg and pa and pv:
                return find_license_in_pom_recursive(pg, pa, pv, check_parent)

            logger.debug(f"No license info found in local POM: {pom_path}, Retry with remote fetch.")

        if not (group_id and artifact_id and version):
            return ''
        return find_license_in_pom_recursive(group_id, artifact_id, version, check_parent)
    except Exception as e:
        logger.warning(f"Error getting license from POM: {e}")
        return ''
