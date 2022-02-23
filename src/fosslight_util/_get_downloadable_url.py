#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import re
from bs4 import BeautifulSoup
from urllib.request import urlopen
import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)


def get_downloadable_url(link):

    ret = False
    new_link = ''

    link = link.replace('http://', '')
    link = link.replace('https://', '')

    if link.startswith('pypi.org/'):
        ret, new_link = get_download_location_for_pypi(link)
    elif link.startswith('mvnrepository.com/artifact/') or link.startswith('repo1.maven.org/'):
        ret, new_link = get_download_location_for_maven(link)
    elif link.startswith('www.npmjs.com/') or link.startswith('registry.npmjs.org'):
        ret, new_link = get_download_location_for_npm(link)
    elif link.startswith('pub.dev/'):
        ret, new_link = get_download_location_for_pub(link)

    return ret, new_link


def get_download_location_for_pypi(link):
    # get the url for downloading source file in pypi.org/project/(oss_name)/(oss_version)/#files
    ret = False
    new_link = ''

    try:
        dn_loc_re = re.findall(r'pypi.org\/project\/?([^\/]*)\/?([^\/]*)', link)
        oss_name = dn_loc_re[0][0]
        oss_version = dn_loc_re[0][1]

        pypi_url = 'https://pypi.org/project/' + oss_name + '/' + oss_version + '/#files'

        content = urlopen(pypi_url).read().decode('utf8')
        bs_obj = BeautifulSoup(content, 'html.parser')

        card_file_list = bs_obj.findAll('div', {'class': 'card file__card'})

        for card_file in card_file_list:
            file_code = card_file.find('code').text
            if file_code == "source":
                new_link = card_file.find('a').attrs['href']
                ret = True
                break
    except Exception as error:
        ret = False
        logger.warning('Cannot find the link for pypi (url:'+link+') '+str(error))

    return ret, new_link


def get_download_location_for_maven(link):
    # get the url for downloading source file in
    # repo1.maven.org/maven2/(group_id(split to separator '/'))/(artifact_id)/(oss_version)
    ret = False
    new_link = ''

    try:
        if link.startswith('mvnrepository.com/artifact/'):
            dn_loc_split = link.replace('mvnrepository.com/', '').split('/')
            group_id = dn_loc_split[1].replace('.', '/')
            dn_loc = 'https://repo1.maven.org/maven2/' + group_id + '/' + dn_loc_split[2] + '/' + dn_loc_split[3]

        elif link.startswith('repo1.maven.org/maven2/'):
            dn_loc_split = link.replace('repo1.maven.org/maven2/', '').split('/')

            if link.endswith('.tar.gz') or link.endswith('.jar') or link.endswith('.tar.xz'):
                new_link = 'https://' + link
                ret = True
                return ret, new_link
            else:
                dn_loc = 'https://' + link
        else:
            raise Exception("not valid url for maven")

        html = urlopen(dn_loc).read().decode('utf8')
        bs_obj = BeautifulSoup(html, 'html.parser')

        file_name = dn_loc.split('/')[-2] + '-' + dn_loc.split('/')[-1] + '-sources.jar'

        for link in bs_obj.findAll("a"):
            if link.text == file_name:
                source_url = link['href']
                new_link = dn_loc + '/' + source_url
                break
            elif link['href'].endswith('sources.jar') or link['href'].endswith('source.jar') or link['href'].endswith('src.jar'):
                source_url = link['href']
                new_link = dn_loc + '/' + source_url

        if new_link != '':
            ret = True

    except Exception as error:
        ret = False
        logger.warning('Cannot find the link for maven (url:'+link+') '+str(error))

    return ret, new_link


def get_download_location_for_npm(link):
    # url format : registry.npmjs.org/packagename/-/packagename-version.tgz
    ret = False
    new_link = ''

    try:
        if link.startswith('www.npmjs.com/') or link.startswith('registry.npmjs.org'):
            dn_loc_split = link.split('/')

            if dn_loc_split[1] == 'package':
                idx = 2
            else:
                idx = 1

            if dn_loc_split[idx].startswith('@'):
                oss_name_npm = dn_loc_split[idx]+'/'+dn_loc_split[idx+1]
                tar_name = dn_loc_split[idx+1] + '-' + dn_loc_split[idx+3]
            else:
                oss_name_npm = dn_loc_split[idx]
                tar_name = oss_name_npm + '-' + dn_loc_split[idx+2]

            new_link = 'https://registry.npmjs.org/' + oss_name_npm + '/-/' + tar_name + '.tgz'
            ret = True

    except Exception as error:
        ret = False
        logger.warning('Cannot find the link for npm (url:'+link+') '+str(error))

    return ret, new_link


def get_download_location_for_pub(link):
    ret = False
    new_link = ''

    # url format : https://pub.dev/packages/(oss_name)/versions/(oss_version)
    # download url format : https://storage.googleapis.com/pub-packages/packages/(oss_name)-(oss_version).tar.gz
    try:
        if link.startswith('pub.dev/packages'):
            dn_loc_split = link.split('/')
            oss_name_pub = dn_loc_split[2]
            oss_version_pub = dn_loc_split[4]

            new_link = 'https://storage.googleapis.com/pub-packages/packages/' + oss_name_pub + '-' + oss_version_pub + '.tar.gz'
            ret = True

    except Exception as error:
        ret = False
        logger.warning('Cannot find the link for npm (url:'+link+') '+str(error))

    return ret, new_link
