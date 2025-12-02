#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import re
import requests
from lastversion import latest
from bs4 import BeautifulSoup
from urllib.request import urlopen
import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)


def version_exists(pkg_type, origin_name, version):
    try:
        if pkg_type in ['npm', 'npm2']:
            r = requests.get(f"https://registry.npmjs.org/{origin_name}", timeout=5)
            if r.status_code == 200:
                data = r.json()
                return version in data.get('versions', {})
        elif pkg_type == 'pypi':
            r = requests.get(f"https://pypi.org/pypi/{origin_name}/{version}/json", timeout=5)
            return r.status_code == 200
        elif pkg_type == 'maven':
            r = requests.get(f'https://api.deps.dev/v3alpha/systems/maven/packages/{origin_name}', timeout=5)
            if r.status_code == 200:
                versions = r.json().get('versions', [])
                for vobj in versions:
                    vkey = vobj.get('versionKey') or {}
                    if vkey.get('version') == version:
                        return True
                return False
        elif pkg_type == 'pub':
            r = requests.get(f'https://pub.dev/api/packages/{origin_name}', timeout=5)
            if r.status_code == 200:
                versions = r.json().get('versions', [])
                return any(v.get('version') == version for v in versions if isinstance(v, dict))
        elif pkg_type == 'go':
            if not version.startswith('v'):
                version = f'v{version}'
            r = requests.get(f'https://proxy.golang.org/{origin_name}/@v/list', timeout=5)
            if r.status_code == 200:
                listed = r.text.splitlines()
                return version in listed
    except Exception as e:
        logger.info(f'version_exists check failed ({pkg_type}:{origin_name}:{version}) {e}')
        return True
    return False


def extract_name_version_from_link(link, checkout_version):
    oss_name = ""
    oss_version = ""
    matched = False
    direct_maven = False

    if link.startswith("www."):
        link = link.replace("www.", "https://www.", 1)

    if (not matched and (
        link.startswith('https://repo1.maven.org/maven2/') or
        link.startswith('https://dl.google.com/android/maven2/')
    )):
        parsed = parse_direct_maven_url(link)
        if parsed:
            origin_name, parsed_version = parsed
            oss_name = origin_name  # groupId:artifactId
            oss_version = parsed_version or ""
            matched = True
            direct_maven = True
            pkg_type = 'maven'

    for direct_key in ["maven_repo1", "maven_google"]:
        pattern = constant.PKG_PATTERN.get(direct_key)
        if pattern and re.match(pattern, link):
            parsed = parse_direct_maven_url(link)
            if parsed:
                origin_name, parsed_version = parsed
                oss_name = origin_name
                oss_version = parsed_version or ""
                matched = True
                direct_maven = True
                pkg_type = 'maven'
                break

    if not matched:
        for key, value in constant.PKG_PATTERN.items():
            if key in ["maven_repo1", "maven_google"]:
                continue
            p = re.compile(value)
            match = p.match(link)
            if match:
                try:
                    pkg_type = key
                    origin_name = match.group(1)
                    if (key == "pypi") or (key == "pypi2"):
                        oss_name = f"pypi:{origin_name}"
                        oss_name = re.sub(r"[-_.]+", "-", oss_name)
                        oss_version = match.group(2)
                        pkg_type = 'pypi'
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
                    elif key == "cocoapods":
                        oss_name = f"cocoapods:{origin_name}"
                    elif key == "go":
                        if origin_name.endswith('/'):
                            origin_name = origin_name[:-1]
                        oss_name = f"go:{origin_name}"
                        oss_version = match.group(2)
                    elif key == "cargo":
                        oss_name = f"cargo:{origin_name}"
                        oss_version = match.group(2)
                except Exception as ex:
                    logger.info(f"extract_name_version_from_link {key}:{ex}")
                if oss_name:
                    matched = True
                break

    if not matched:
        return "", "", link, ""
    else:
        need_latest = False
        if not oss_version and checkout_version:
            oss_version = checkout_version.strip()
        if pkg_type in ["pypi", "maven", "npm", "npm2", "pub", "go"]:
            if oss_version:
                try:
                    if not version_exists(pkg_type, origin_name, oss_version):
                        logger.info(f'Version {oss_version} not found for {oss_name}; will attempt latest fallback')
                        need_latest = True
                except Exception as e:
                    logger.info(f'Version validation failed ({oss_name}:{oss_version}) {e}; will attempt latest fallback')
                    need_latest = True
            else:
                need_latest = True
        if need_latest:
            latest_ver = get_latest_package_version(link, pkg_type, origin_name)
            if latest_ver:
                if oss_version and latest_ver != oss_version:
                    logger.info(f'Fallback to latest version {latest_ver} (previous invalid: {oss_version})')
                elif not oss_version:
                    logger.info(f'Using latest version {latest_ver} (no version detected)')
                oss_version = latest_ver

    try:
        if oss_version:
            if pkg_type == 'maven' and direct_maven:
                # Skip if oss_name malformed
                if ':' in oss_name:
                    parts = oss_name.split(':', 1)
                    group_id, artifact_id = parts[0], parts[1]
                    group_path = group_id.replace('.', '/')
                    if (
                        link.startswith('https://repo1.maven.org/maven2/') or
                        link.startswith('http://repo1.maven.org/maven2/')
                    ):
                        if not re.search(r'/\d[^/]*/*$', link.rstrip('/')):
                            link = (
                                f'https://repo1.maven.org/maven2/{group_path}/'
                                f'{artifact_id}/{oss_version}'
                            )
                    elif (
                        link.startswith('https://dl.google.com/android/maven2/') or
                        link.startswith('http://dl.google.com/android/maven2/')
                    ):
                        if not re.search(r'/\d[^/]*/*$', link.rstrip('/')):
                            link = (
                                f'https://dl.google.com/android/maven2/{group_path}/'
                                f'{artifact_id}/{oss_version}/{artifact_id}-{oss_version}-sources.jar'
                            )
                else:
                    logger.debug(f'Skip maven normalization due to invalid oss_name: {oss_name}')
            else:
                link = get_new_link_with_version(link, pkg_type, origin_name, oss_version)
    except Exception as _e:
        logger.info(f'Failed to build versioned link for {oss_name or origin_name}:{oss_version} {_e}')

    return oss_name, oss_version, link, pkg_type


def parse_direct_maven_url(url):
    try:
        clean_url = url.replace('https://', '').replace('http://', '')
        if clean_url.startswith('repo1.maven.org/maven2/'):
            base_path = clean_url[len('repo1.maven.org/maven2/'):]
        elif clean_url.startswith('dl.google.com/android/maven2/'):
            base_path = clean_url[len('dl.google.com/android/maven2/'):]
        else:
            return None

        base_path = base_path.rstrip('/')
        # Strip file name if ends with known artifact extension.
        if any(base_path.endswith(ext) for ext in ['.jar', '.pom', '.aar']):
            base_path = '/'.join(base_path.split('/')[:-1])

        parts = base_path.split('/')
        if len(parts) < 2:
            return None

        version = None
        artifact_id = None
        if len(parts) >= 3:
            potential_version = parts[-1]
            potential_artifact = parts[-2]
            if re.search(r'\d', potential_version):
                version = potential_version
                artifact_id = potential_artifact
                group_parts = parts[:-2]
            else:
                artifact_id = parts[-1]
                group_parts = parts[:-1]
        else:
            artifact_id = parts[-1]
            group_parts = parts[:-1]

        group_id = '.'.join(group_parts)
        if not group_id or not artifact_id:
            return None

        maven_name = f"{group_id}:{artifact_id}"
        return maven_name, version
    except Exception as e:
        logger.debug(f'Failed to parse direct Maven URL {url}: {e}')
        return None


def get_new_link_with_version(link, pkg_type, oss_name, oss_version):
    if pkg_type == "pypi":
        link = f'https://pypi.org/project/{oss_name}/{oss_version}'
    elif pkg_type == "maven":
        oss_name = oss_name.replace(':', '/')
        link = f'https://mvnrepository.com/artifact/{oss_name}/{oss_version}'
    elif pkg_type == "npm" or pkg_type == "npm2":
        link = f'https://www.npmjs.com/package/{oss_name}/v/{oss_version}'
    elif pkg_type == "pub":
        link = f'https://pub.dev/packages/{oss_name}/versions/{oss_version}'
    elif pkg_type == "go":
        if not oss_version.startswith('v'):
            oss_version = f'v{oss_version}'
        link = f'https://pkg.go.dev/{oss_name}@{oss_version}'
    elif pkg_type == "cargo":
        link = f'https://crates.io/crates/{oss_name}/{oss_version}'
    return link


def get_latest_package_version(link, pkg_type, oss_name):
    find_version = ''

    try:
        if pkg_type in ['npm', 'npm2']:
            npm_response = requests.get(f"https://registry.npmjs.org/{oss_name}")
            if npm_response.status_code == 200:
                find_version = npm_response.json().get("dist-tags", {}).get("latest")
        elif pkg_type == 'pypi':
            find_version = str(latest(oss_name, at='pip', output_format='version', pre_ok=True))
        elif pkg_type == 'maven':
            maven_response = requests.get(f'https://api.deps.dev/v3alpha/systems/maven/packages/{oss_name}')
            if maven_response.status_code == 200:
                versions = maven_response.json().get('versions', [])
                if versions:
                    # Some version entries may miss publishedAt; fallback to semantic version ordering.
                    def sem_key(vstr: str):
                        # Parse semantic version with optional prerelease label
                        # Examples: 1.9.0, 1.10.0-alpha, 2.0.0-rc
                        m = re.match(r'^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-.]([A-Za-z0-9]+))?$', vstr)
                        if not m:
                            return (0, 0, 0, 999)
                        major = int(m.group(1) or 0)
                        minor = int(m.group(2) or 0)
                        patch = int(m.group(3) or 0)
                        label = (m.group(4) or '').lower()
                        # Assign label weights: stable > rc > beta > alpha
                        label_weight_map = {
                            'alpha': -3,
                            'beta': -2,
                            'rc': -1
                        }
                        weight = label_weight_map.get(label, 0 if label == '' else -4)
                        return (major, minor, patch, weight)

                    with_pub = [v for v in versions if v.get('publishedAt')]
                    if with_pub:
                        cand = max(with_pub, key=lambda v: v.get('publishedAt'))
                    else:
                        decorated = []
                        for v in versions:
                            vkey = v.get('versionKey', {})
                            ver = vkey.get('version', '')
                            if ver:
                                decorated.append((sem_key(ver), ver, v))
                        if decorated:
                            decorated.sort(key=lambda t: t[0])
                            stable_candidates = [t for t in decorated if t[0][3] == 0]
                            if stable_candidates:
                                cand = stable_candidates[-1][2]
                            else:
                                cand = decorated[-1][2]
                        else:
                            cand = versions[-1]
                    find_version = cand.get('versionKey', {}).get('version', '')
        elif pkg_type == 'pub':
            pub_response = requests.get(f'https://pub.dev/api/packages/{oss_name}')
            if pub_response.status_code == 200:
                find_version = pub_response.json().get('latest').get('version')
        elif pkg_type == 'go':
            go_response = requests.get(f'https://proxy.golang.org/{oss_name}/@latest')
            if go_response.status_code == 200:
                find_version = go_response.json().get('Version')
                if find_version.startswith('v'):
                    find_version = find_version[1:]
    except Exception as e:
        logger.info(f'Fail to get latest package version({link}:{e})')
    return find_version


def get_downloadable_url(link, checkout_version):

    ret = False
    result_link = link

    oss_name, oss_version, new_link, pkg_type = extract_name_version_from_link(link, checkout_version)
    new_link = new_link.replace('http://', '')
    new_link = new_link.replace('https://', '')

    if pkg_type == "pypi":
        ret, result_link = get_download_location_for_pypi(new_link)
    elif pkg_type == "maven" or new_link.startswith('repo1.maven.org/') or new_link.startswith('dl.google.com/android/maven2/'):
        ret, result_link = get_download_location_for_maven(new_link)
    elif (pkg_type in ["npm", "npm2"]) or new_link.startswith('registry.npmjs.org/'):
        ret, result_link = get_download_location_for_npm(new_link)
    elif pkg_type == "pub":
        ret, result_link = get_download_location_for_pub(new_link)
    elif pkg_type == "go":
        ret, result_link = get_download_location_for_go(new_link)
    elif pkg_type == "cargo":
        ret, result_link = get_download_location_for_cargo(new_link)
    return ret, result_link, oss_name, oss_version, pkg_type


def get_download_location_for_cargo(link):
    # get the url for downloading source file: https://crates.io/api/v1/crates/<name>/<version>/download
    ret = False
    new_link = ''
    host = 'https://crates.io/api/v1/crates'

    try:
        dn_loc_re = re.findall(r'crates.io\/crates\/([^\/]+)\/?([^\/]*)', link)
        if dn_loc_re:
            oss_name = dn_loc_re[0][0]
            oss_version = dn_loc_re[0][1]

            new_link = f'{host}/{oss_name}/{oss_version}/download'
            res = urlopen(new_link)
            if res.getcode() == 200:
                ret = True
            else:
                logger.warning(f'Cannot find the valid link for cargo (url:{new_link}')
    except Exception as error:
        ret = False
        logger.warning(f'Cannot find the link for cargo (url:{link}({(new_link)})): {error}')

    return ret, new_link


def get_download_location_for_go(link):
    # get the url for downloading source file: https://proxy.golang.org/<module>/@v/VERSION.zip
    ret = False
    new_link = ''
    host = 'https://proxy.golang.org'

    try:
        dn_loc_re = re.findall(r'pkg.go.dev\/([^\@]+)\@?([^\/]*)', link)
        if dn_loc_re:
            oss_name = dn_loc_re[0][0]
            if oss_name.endswith('/'):
                oss_name = oss_name[:-1]
            oss_version = dn_loc_re[0][1]

            new_link = f'{host}/{oss_name}/@v/{oss_version}.zip'
        try:
            res = urlopen(new_link)
            if res.getcode() == 200:
                ret = True
            else:
                logger.warning(f'Cannot find the valid link for go (url:{new_link}')
        except Exception as e:
            logger.warning(f'Fail to find the valid link for go (url:{new_link}: {e}')
    except Exception as error:
        ret = False
        logger.warning(f'Cannot find the link for go (url:{link}({(new_link)})): {error}')

    return ret, new_link


def get_available_wheel_urls(name, version):
    try:
        api_url = f'https://pypi.org/pypi/{name}/{version}/json'
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            wheel_urls = []

            for file_info in data.get('urls', []):
                if file_info.get('packagetype') == 'bdist_wheel':
                    wheel_urls.append(file_info.get('url'))

            return wheel_urls
        else:
            logger.warning(f'Cannot get PyPI API data for {name}({version})')
            return []

    except Exception as error:
        logger.warning(f'Failed to get wheel URLs from PyPI API: {error}')
        return []


def get_download_location_for_pypi(link):
    # get the url for downloading source file: https://docs.pypi.org/api/ Predictable URLs
    ret = False
    new_link = ''
    host = 'https://files.pythonhosted.org'

    try:
        dn_loc_re = re.findall(r'pypi.org\/project\/?([^\/]*)\/?([^\/]*)', link)
        oss_name = dn_loc_re[0][0]
        oss_name = re.sub(r"[-_.]+", "-", oss_name)
        oss_version = dn_loc_re[0][1]

        # 1. Source distribution 시도
        new_link = f'{host}/packages/source/{oss_name[0]}/{oss_name}/{oss_name}-{oss_version}.tar.gz'
        try:
            res = urlopen(new_link)
            if res.getcode() == 200:
                ret = True
                return ret, new_link
        except Exception:
            oss_name = re.sub(r"[-]+", "_", oss_name)
            new_link = f'{host}/packages/source/{oss_name[0]}/{oss_name}/{oss_name}-{oss_version}.tar.gz'
            try:
                res = urlopen(new_link)
                if res.getcode() == 200:
                    ret = True
                    return ret, new_link
            except Exception:
                pass

        # 2. Source distribution이 없으면 wheel 파일들을 시도
        wheel_urls = get_available_wheel_urls(oss_name, oss_version)

        if wheel_urls:
            # Pure Python wheel을 우선적으로 찾기
            for wheel_url in wheel_urls:
                if 'py3-none-any' in wheel_url or 'py2.py3-none-any' in wheel_url:
                    try:
                        res = urlopen(wheel_url)
                        if res.getcode() == 200:
                            ret = True
                            new_link = wheel_url
                            logger.info(f'Using wheel file : {wheel_url}')
                            return ret, new_link
                    except Exception:
                        continue

            # Pure Python wheel이 없으면 첫 번째 wheel 시도
            if wheel_urls:
                try:
                    res = urlopen(wheel_urls[0])
                    if res.getcode() == 200:
                        ret = True
                        new_link = wheel_urls[0]
                        logger.info(f'Using wheel file : {wheel_urls[0]}')
                        return ret, new_link
                except Exception:
                    pass

    except Exception as error:
        ret = False
        logger.warning(f'Cannot find the link for pypi (url:{link}({new_link})) e:{str(error)}')

    return ret, new_link


def get_download_location_for_maven(link):
    # get the url for downloading source file in
    # repo1.maven.org/maven2/(group_id(split to separator '/'))/(artifact_id)/(oss_version)
    ret = False
    new_link = ''

    try:
        if link.startswith('mvnrepository.com/artifact/'):
            parts = link.replace('mvnrepository.com/artifact/', '').split('/')
            if len(parts) < 2:
                raise Exception('invalid mvnrepository artifact url')
            group_raw = parts[0]
            artifact_id = parts[1]
            version = parts[2] if len(parts) > 2 and parts[2] else ''
            group_path = group_raw.replace('.', '/')

            repo_base = f'https://repo1.maven.org/maven2/{group_path}/{artifact_id}'
            try:
                urlopen(repo_base)
                if version:
                    dn_loc = f'{repo_base}/{version}'
                else:
                    new_link = repo_base
                    ret = True
                    return ret, new_link
            except Exception:
                google_base = f'https://dl.google.com/android/maven2/{group_path}/{artifact_id}'
                if version:
                    google_sources = f'{google_base}/{version}/{artifact_id}-{version}-sources.jar'
                    try:
                        res_g = urlopen(google_sources)
                        if res_g.getcode() == 200:
                            ret = True
                            return ret, google_sources
                    except Exception:
                        pass
                new_link = google_base
                ret = True
                return ret, new_link

        elif link.startswith('repo1.maven.org/maven2/'):
            if link.endswith('.tar.gz') or link.endswith('.jar') or link.endswith('.tar.xz'):
                new_link = 'https://' + link
                ret = True
                return ret, new_link
            else:
                dn_loc = 'https://' + link
        elif link.startswith('dl.google.com/android/maven2/'):
            if link.endswith('.jar'):
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
