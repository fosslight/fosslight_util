#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import re
import requests
from npm.bindings import npm_run
from lastversion import latest
from bs4 import BeautifulSoup
from urllib.request import urlopen
import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)


def extract_name_version_from_link(link):
    # Github : https://github.com/(owner)/(repo)
    # npm : https://www.npmjs.com/package/(package)/v/(version)
    # npm2 : https://www.npmjs.com/package/@(group)/(package)/v/(version)
    # pypi : https://pypi.org/project/(oss_name)/(version)
    # pypi2 : https://files.pythonhosted.org/packages/source/(alphabet)/(oss_name)/(oss_name)-(version).tar.gz
    # Maven: https://mvnrepository.com/artifact/(group)/(artifact)/(version)
    # pub: https://pub.dev/packages/(package)/versions/(version)
    # Cocoapods: https://cocoapods.org/(package)
    pkg_pattern = {
        "pypi": r'https?:\/\/pypi\.org\/project\/([^\/]+)[\/]?([^\/]*)',
        "pypi2": r'https?:\/\/files\.pythonhosted\.org\/packages\/source\/[\w]\/([^\/]+)\/[\S]+-([^\-]+)\.tar\.gz',
        "maven": r'https?:\/\/mvnrepository\.com\/artifact\/([^\/]+)\/([^\/]+)\/?([^\/]*)',
        "npm": r'https?:\/\/www\.npmjs\.com\/package\/([^\/\@]+)(?:\/v\/)?([^\/]*)',
        "npm2": r'https?:\/\/www\.npmjs\.com\/package\/(\@[^\/]+\/[^\/]+)(?:\/v\/)?([^\/]*)',
        "pub": r'https?:\/\/pub\.dev\/packages\/([^\/]+)(?:\/versions\/)?([^\/]*)',
        "pods": r'https?:\/\/cocoapods\.org\/pods\/([^\/]+)'
    }
    oss_name = ""
    oss_version = ""
    if link.startswith("www."):
        link = link.replace("www.", "https://www.", 1)
    for key, value in pkg_pattern.items():
        p = re.compile(value)
        match = p.match(link)
        if match:
            try:
                origin_name = match.group(1)
                if (key == "pypi") or (key == "pypi2"):
                    oss_name = f"pypi:{origin_name}"
                    oss_name = re.sub(r"[-_.]+", "-", oss_name).lower()
                    oss_version = match.group(2)
                elif key == "maven":
                    artifact = match.group(2)
                    oss_name = f"{origin_name}:{artifact}"
                    origin_name = oss_name
                    oss_version = match.group(3)
                elif key == "npm" or key == "npm2":
                    oss_name = f"npm:{origin_name}"
                    oss_version = match.group(2)
                elif key == "pub":
                    oss_name = f"pub:{origin_name}"
                    oss_version = match.group(2)
                elif key == "pods":
                    oss_name = f"cocoapods:{origin_name}"
            except Exception as ex:
                logger.info(f"extract_name_version_from_link {key}:{ex}")
            if oss_name and (not oss_version):
                if key in ["pypi", "maven", "npm", "npm2", "pub"]:
                    oss_version, link = get_latest_package_version(link, key, origin_name)
                    logger.debug(f'Try to download with the latest version:{link}')
            break
    return oss_name, oss_version, link, key


def get_latest_package_version(link, pkg_type, oss_name):
    find_version = ''
    link_with_version = link

    try:
        if pkg_type in ['npm', 'npm2']:
            stderr, stdout = npm_run('view', oss_name, 'version')
            if stdout:
                find_version = stdout.strip()
            link_with_version = f'https://www.npmjs.com/package/{oss_name}/v/{find_version}'
        elif pkg_type == 'pypi':
            find_version = str(latest(oss_name, at='pip', output_format='version', pre_ok=True))
            link_with_version = f'https://pypi.org/project/{oss_name}/{find_version}'
        elif pkg_type == 'maven':
            maven_response = requests.get(f'https://api.deps.dev/v3alpha/systems/maven/packages/{oss_name}')
            if maven_response.status_code == 200:
                find_version = maven_response.json().get('versions')[-1].get('versionKey').get('version')
            oss_name = oss_name.replace(':', '/')
            link_with_version = f'https://mvnrepository.com/artifact/{oss_name}/{find_version}'
        elif pkg_type == 'pub':
            pub_response = requests.get(f'https://pub.dev/api/packages/{oss_name}')
            if pub_response.status_code == 200:
                find_version = pub_response.json().get('latest').get('version')
            link_with_version = f'https://pub.dev/packages/{oss_name}/versions/{find_version}'
    except Exception as e:
        logger.debug(f'Fail to get latest package version({link}:{e})')
    return find_version, link_with_version


def get_downloadable_url(link):

    ret = False
    result_link = link

    oss_name, oss_version, new_link, pkg_type = extract_name_version_from_link(link)
    new_link = new_link.replace('http://', '')
    new_link = new_link.replace('https://', '')

    if pkg_type == "pypi":
        ret, result_link = get_download_location_for_pypi(new_link)
    elif pkg_type == "maven" or new_link.startswith('repo1.maven.org/'):
        ret, result_link = get_download_location_for_maven(new_link)
    elif (pkg_type in ["npm", "npm2"]) or new_link.startswith('registry.npmjs.org/'):
        ret, result_link = get_download_location_for_npm(new_link)
    elif pkg_type == "pub":
        ret, result_link = get_download_location_for_pub(new_link)

    return ret, result_link, oss_name, oss_version


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
    oss_version = ""
    oss_name_npm = ""
    tar_name = ""

    link = link.replace('%40', '@')
    if link.startswith('www.npmjs.com/') or link.startswith('registry.npmjs.org/'):
        try:
            dn_loc_split = link.split('/')
            if dn_loc_split[1] == 'package':
                idx = 2
            else:
                idx = 1
            if dn_loc_split[idx].startswith('@'):
                oss_name_npm = dn_loc_split[idx]+'/'+dn_loc_split[idx+1]
                tar_name = dn_loc_split[idx+1]
                oss_version = dn_loc_split[idx+3]
            else:
                oss_name_npm = dn_loc_split[idx]
                tar_name = oss_name_npm
                oss_version = dn_loc_split[idx+2]

            tar_name = f'{tar_name}-{oss_version}'
            new_link = f'https://registry.npmjs.org/{oss_name_npm}/-/{tar_name}.tgz'
            ret = True
        except Exception as error:
            ret = False
            logger.warning('Cannot find the link for npm (url:'+link+') '+str(error))
    return ret, new_link


def get_download_location_for_pub(link):
    ret = False
    new_link = ''

    # url format : https://pub.dev/packages/(oss_name)/versions/(oss_version)
    # download url format : https://pub.dev/packages/(oss_name)/versions/(oss_version).tar.gz
    try:
        if link.startswith('pub.dev/packages'):
            new_link = f'https://{link}.tar.gz'
            ret = True

    except Exception as error:
        ret = False
        logger.warning('Cannot find the link for pub (url:'+link+') '+str(error))

    return ret, new_link
