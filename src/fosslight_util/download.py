#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import sys
import wget
import tarfile
import zipfile
import logging
import argparse
import shutil
from git import Repo, GitCommandError, Git
import bz2
import contextlib
from datetime import datetime
from pathlib import Path
from fosslight_util._get_downloadable_url import get_downloadable_url
from fosslight_util.help import print_help_msg_download
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
import signal
import time
import threading
import platform
import subprocess
import re
from typing import Tuple
import urllib.parse
import json

logger = logging.getLogger(constant.LOGGER_NAME)
compression_extension = {".tar.bz2", ".tar.gz", ".tar.xz", ".tgz", ".tar", ".zip", ".jar", ".bz2"}
prefix_refs = ["refs/remotes/origin/", "refs/tags/"]
SIGNAL_TIMEOUT = 600


class Alarm(threading.Thread):
    def __init__(self, timeout):
        threading.Thread.__init__(self)
        self.timeout = timeout
        self.setDaemon(True)

    def run(self):
        time.sleep(self.timeout)
        logger.error("download timeout! (%d sec)", SIGNAL_TIMEOUT)
        os._exit(1)


class TimeOutException(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code


def alarm_handler(signum, frame):
    logger.warning("download timeout! (%d sec)", SIGNAL_TIMEOUT)
    raise TimeOutException(f'Timeout ({SIGNAL_TIMEOUT} sec)', 1)


def change_src_link_to_https(src_link):
    src_link = src_link.replace("git://", "https://")
    if src_link.endswith(".git"):
        src_link = src_link.replace('.git', '')
    return src_link


def change_ssh_link_to_https(src_link):
    src_link = src_link.replace("git@github.com:", "https://github.com/")
    return src_link


def parse_src_link(src_link):
    src_info = {"url": src_link}
    src_link_changed = ""
    if src_link.startswith("git://") or src_link.startswith("git@") \
            or src_link.startswith("https://") or src_link.startswith("http://"):
        src_link_split = src_link.split(';')
        if src_link.startswith("git://github.com/"):
            src_link_changed = change_src_link_to_https(src_link_split[0])
        elif src_link.startswith("git@github.com:"):
            src_link_changed = src_link_split[0]
        else:
            if "rubygems.org" in src_link:
                src_info["rubygems"] = True
            src_link_changed = src_link_split[0]

        branch_info = [s for s in src_link_split if s.startswith('branch')]
        tag_info = [s for s in src_link_split if s.startswith('tag')]

        src_info["url"] = src_link_changed
        src_info["branch"] = branch_info
        src_info["tag"] = tag_info
    return src_info


def cli_download_and_extract(link: str, target_dir: str, log_dir: str, checkout_to: str = "",
                             compressed_only: bool = False, ssh_key: str = "",
                             id: str = "", git_token: str = "",
                             called_cli: bool = True,
                             output: bool = False) -> Tuple[bool, str, str, str]:
    global logger

    success = True
    msg = ""
    msg_wget = ""
    oss_name = ""
    oss_version = ""
    log_file_name = "fosslight_download_" + \
        datetime.now().strftime('%Y%m%d_%H-%M-%S')+".txt"
    logger, log_item = init_log(os.path.join(log_dir, log_file_name))
    link = link.strip()
    is_rubygems = False

    try:
        if not link:
            success = False
            msg = "Need a link to download."
        elif os.path.isfile(target_dir):
            success = False
            msg = f"The target directory exists as a file.: {target_dir}"
        else:
            src_info = parse_src_link(link)
            link = src_info.get("url", "")
            tag = ''.join(src_info.get("tag",  "")).split('=')[-1]
            branch = ''.join(src_info.get("branch", "")).split('=')[-1]
            is_rubygems = src_info.get("rubygems", False)

            # General download (git clone, wget)
            success_git, msg, oss_name, oss_version = download_git_clone(link, target_dir,
                                                                         checkout_to,
                                                                         tag, branch,
                                                                         ssh_key, id, git_token,
                                                                         called_cli)
            link = change_ssh_link_to_https(link)
            if (not is_rubygems) and (not success_git):
                if os.path.isfile(target_dir):
                    shutil.rmtree(target_dir)

                success, downloaded_file, msg_wget, oss_name, oss_version = download_wget(link, target_dir, compressed_only)
                if success:
                    success = extract_compressed_file(downloaded_file, target_dir, True, compressed_only)
            # Download from rubygems.org
            elif is_rubygems and shutil.which("gem"):
                success = gem_download(link, target_dir, checkout_to)
        if msg:
            msg = f'git fail: {msg}'
            if is_rubygems:
                msg = f'gem download: {success}'
            else:
                if msg_wget:
                    msg = f'{msg}, wget fail: {msg_wget}'
                else:
                    msg = f'{msg}, wget success'

    except Exception as error:
        success = False
        msg = str(error)

    if output:
        output_result = {
            "success": success,
            "message": msg,
            "oss_name": oss_name,
            "oss_version": oss_version
        }
        output_json = os.path.join(log_dir, "fosslight_download_output.json")
        with open(output_json, 'w') as f:
            json.dump(output_result, f, indent=4)

    logger.info(f"\n* FOSSLight Downloader - Result: {success} ({msg})")
    return success, msg, oss_name, oss_version


def get_ref_to_checkout(checkout_to, ref_list):
    ref_to_checkout = checkout_to
    try:
        checkout_to = checkout_to.strip()
        if checkout_to in ref_list:
            return checkout_to

        for prefix in prefix_refs:
            ref_to_checkout = prefix+checkout_to
            if ref_to_checkout in ref_list:
                return ref_to_checkout

        ref_to_checkout = next(
            x for x in ref_list if x.endswith(checkout_to))
    except Exception as error:
        logger.warning(f"git find ref - failed: {error}")
    return ref_to_checkout


def decide_checkout(checkout_to="", tag="", branch=""):
    if checkout_to:
        ref_to_checkout = checkout_to
    else:
        if branch:
            ref_to_checkout = branch
        else:
            ref_to_checkout = tag
    return ref_to_checkout


def get_github_ossname(link):
    oss_name = ""
    p = re.compile(r'https?:\/\/github.com\/([^\/]+)\/([^\/\.]+)(\.git)?')
    match = p.match(link)
    if match:
        oss_name = f"{match.group(1)}-{match.group(2)}"
    return oss_name


def get_github_token(git_url):
    github_token = ""
    pattern = r'https://(.*?)@'
    search = re.search(pattern, git_url)
    if search:
        github_token = search.group(1)
    return github_token


def download_git_repository(refs_to_checkout, git_url, target_dir, tag, called_cli=True):
    success = False
    oss_version = ""

    logger.info(f"Download git url :{git_url}")
    env = os.environ.copy()
    if not called_cli:
        env["GIT_TERMINAL_PROMPT"] = "0"
    if refs_to_checkout:
        try:
            # gitPython uses the branch argument the same whether you check out to a branch or a tag.
            Repo.clone_from(git_url, target_dir, branch=refs_to_checkout, env=env)
            if any(Path(target_dir).iterdir()):
                success = True
                oss_version = refs_to_checkout
                logger.info(f"Files found in {target_dir} after clone.")
            else:
                logger.info(f"No files found in {target_dir} after clone.")
                success = False
        except GitCommandError as error:
            logger.info(f"Git checkout error:{error}")
            success = False
        except Exception as e:
            logger.info(f"Repo.clone_from error:{e}")
            success = False

    if not success:
        Repo.clone_from(git_url, target_dir, env=env)
        if any(Path(target_dir).iterdir()):
            success = True
        else:
            logger.info(f"No files found in {target_dir} after clone.")
            success = False
    return success, oss_version


def download_git_clone(git_url, target_dir, checkout_to="", tag="", branch="",
                       ssh_key="", id="", git_token="", called_cli=True):
    oss_name = get_github_ossname(git_url)
    refs_to_checkout = decide_checkout(checkout_to, tag, branch)
    msg = ""
    success = True

    try:
        if platform.system() != "Windows":
            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(SIGNAL_TIMEOUT)
        else:
            alarm = Alarm(SIGNAL_TIMEOUT)
            alarm.start()

        Path(target_dir).mkdir(parents=True, exist_ok=True)

        if git_url.startswith("ssh:") and not ssh_key:
            msg = "Private git needs ssh_key"
            success = False
        else:
            if ssh_key:
                logger.info(f"Download git with ssh_key:{git_url}")
                git_ssh_cmd = f'ssh -i {ssh_key}'
                with Git().custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
                    success, oss_version = download_git_repository(refs_to_checkout, git_url, target_dir, tag, called_cli)
            else:
                if id and git_token:
                    try:
                        m = re.match(r"^(ht|f)tp(s?)\:\/\/", git_url)
                        protocol = m.group()
                        if protocol:
                            encoded_git_token = urllib.parse.quote(git_token, safe='')
                            encoded_id = urllib.parse.quote(id, safe='')
                            git_url = git_url.replace(protocol, f"{protocol}{encoded_id}:{encoded_git_token}@")
                    except Exception as error:
                        logger.info(f"Failed to insert id, token to git url:{error}")
                success, oss_version = download_git_repository(refs_to_checkout, git_url, target_dir, tag, called_cli)

            logger.info(f"git checkout: {oss_version}")
            refs_to_checkout = oss_version

            if platform.system() != "Windows":
                signal.alarm(0)
            else:
                del alarm
    except Exception as error:
        success = False
        logger.warning(f"git clone - failed: {error}")
        msg = str(error)

    return success, msg, oss_name, refs_to_checkout


def download_wget(link, target_dir, compressed_only):
    success = False
    msg = ""
    oss_name = ""
    oss_version = ""
    downloaded_file = ""

    try:
        if platform.system() != "Windows":
            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(SIGNAL_TIMEOUT)
        else:
            alarm = Alarm(SIGNAL_TIMEOUT)
            alarm.start()

        Path(target_dir).mkdir(parents=True, exist_ok=True)

        ret, new_link, oss_name, oss_version, pkg_type = get_downloadable_url(link)
        if ret and new_link:
            link = new_link

        if compressed_only:
            for ext in compression_extension:
                if link.endswith(ext):
                    success = True
                    break
            if not success:
                if pkg_type == 'cargo':
                    success = True
        else:
            success = True

        if not success:
            raise Exception('Not supported compression type (link:{0})'.format(link))

        logger.info(f"wget: {link}")
        if pkg_type == 'cargo':
            outfile = os.path.join(target_dir, f'{oss_name}.tar.gz')
            downloaded_file = wget.download(link, out=outfile)
        else:
            downloaded_file = wget.download(link, target_dir)
        if platform.system() != "Windows":
            signal.alarm(0)
        else:
            del alarm

        if downloaded_file:
            success = True
            logger.debug(f"wget - downloaded: {downloaded_file}")
    except Exception as error:
        success = False
        msg = str(error)
        logger.warning(f"wget - failed: {error}")

    return success, downloaded_file, msg, oss_name, oss_version


def extract_compressed_dir(src_dir, target_dir, remove_after_extract=True):
    logger.debug(f"Extract Dir: {src_dir}")
    try:
        files_path = [os.path.join(src_dir, x) for x in os.listdir(src_dir)]
        for fname in files_path:
            extract_compressed_file(fname, target_dir, remove_after_extract, True)
    except Exception as error:
        logger.debug(f"Extract files in dir - failed: {error}")
        return False
    return True


def extract_compressed_file(fname, extract_path, remove_after_extract=True, compressed_only=True):
    success = True
    try:
        is_compressed_file = True
        if os.path.isfile(fname):
            if fname.endswith(".tar.bz2"):
                decompress_bz2(fname, extract_path)
                os.remove(fname)
                fname = os.path.splitext(fname)[0]

            if fname.endswith(".tar.gz") or fname.endswith(".tgz"):
                with contextlib.closing(tarfile.open(fname, "r:gz")) as t:
                    t.extractall(path=extract_path)
            elif fname.endswith(".tar.xz") or fname.endswith(".tar"):
                with contextlib.closing(tarfile.open(fname, "r:*")) as t:
                    t.extractall(path=extract_path)
            elif fname.endswith(".zip") or fname.endswith(".jar"):
                unzip(fname, extract_path)
            elif fname.endswith(".bz2"):
                decompress_bz2(fname, extract_path)
            else:
                is_compressed_file = False
                if compressed_only:
                    success = False
                logger.warning(f"Unsupported file extension: {fname}")

            if remove_after_extract and is_compressed_file:
                logger.debug(f"Remove - extracted file: {fname}")
                os.remove(fname)
        else:
            logger.warning(f"Not a file: {fname}")
    except Exception as error:
        logger.error(f"Extract - failed: {error}")
        success = False
    return success


def decompress_bz2(source_file, dest_path):
    try:
        fzip = bz2.BZ2File(source_file)
        data = fzip.read()  # get the decompressed data
        with open(os.path.splitext(source_file)[0], 'wb') as f:
            f.write(data)  # write a uncompressed file

    except Exception as error:
        logger.error(f"Decompress bz2 - failed: {error}")
        return False
    return True


def unzip(source_file, dest_path):
    try:
        fzip = zipfile.ZipFile(source_file, 'r')
        for filename in fzip.namelist():
            fzip.extract(filename, dest_path)
        fzip.close()
    except Exception as error:
        logger.error(f"Unzip - failed: {error}")
        return False
    return True


def get_gem_version(checkout_to, ver_in_url=""):
    gem_ver = ""
    ver_found = False
    if checkout_to:
        ver_found = True
        gem_ver = checkout_to
    elif ver_in_url:
        ver_found = True
        gem_ver = ver_in_url
    return gem_ver, ver_found


def gem_download(link, target_dir, checkout_to):
    ver_in_url = ""
    success = True
    try:
        # EX) https://rubygems.org/gems/json/versions/2.6.2 -> get 'json'
        gem_name = link.split("rubygems.org/gems/")[-1].split('/')[0]
        # Ex) if version info. is included in url, json/versions/2.6.2 -> get '2.6.2'
        if 'versions/' in link:
            ver_in_url = link.split('versions/')[-1]
        gem_ver, ver_found = get_gem_version(checkout_to, ver_in_url)

        # gem fetch
        if ver_found:
            fetch_cmd = ['gem', 'fetch', gem_name, '-v', gem_ver]
        else:
            fetch_cmd = ['gem', 'fetch', gem_name]
        fetch_result = subprocess.check_output(fetch_cmd, universal_newlines=True)
        fetch_result = fetch_result.replace('\n', '').split(' ')[-1]
        downloaded_gem = f"{fetch_result}.gem"
        if not os.path.isfile(downloaded_gem):
            success = False
        else:
            # gem unpack
            subprocess.check_output(['gem', 'unpack', downloaded_gem], universal_newlines=True)
            # move unpacked file to target directory
            shutil.move(fetch_result, target_dir)
    except Exception as error:
        success = False
        logger.warning(f"gem download - failed: {error}")
    return success


def main():
    parser = argparse.ArgumentParser(description='FOSSLight Downloader', prog='fosslight_download', add_help=False)
    parser.add_argument('-h', '--help', help='Print help message', action='store_true', dest='help')
    parser.add_argument('-s', '--source', help='Source link to download', type=str, dest='source')
    parser.add_argument('-t', '--target_dir', help='Target directory', type=str, dest='target_dir', default="")
    parser.add_argument('-d', '--log_dir', help='Directory to save log file', type=str, dest='log_dir', default="")
    parser.add_argument('-c', '--checkout_to', help='Checkout to  branch or tag', type=str, dest='checkout_to', default="")
    parser.add_argument('-z', '--compressed_only', help='Unzip only compressed file',
                        action='store_true', dest='compressed_only', default=False)
    parser.add_argument('-o', '--output', help='Generate output file', action='store_true', dest='output', default=False)

    src_link = ""
    target_dir = os.getcwd()
    log_dir = os.getcwd()
    checkout_to = ""
    compressed_only = False
    output = False

    try:
        args = parser.parse_args()
    except SystemExit:
        sys.exit(0)

    if args.help:
        print_help_msg_download()
    if args.source:
        src_link = args.source
    if args.target_dir:
        target_dir = args.target_dir
    if args.log_dir:
        log_dir = args.log_dir
    if args.checkout_to:
        checkout_to = args.checkout_to
    if args.compressed_only:
        compressed_only = args.compressed_only
    if args.output:
        output = args.output

    if not src_link:
        print_help_msg_download()
    else:
        cli_download_and_extract(src_link, target_dir, log_dir, checkout_to,
                                 compressed_only, "", "", "", False,
                                 output)


if __name__ == '__main__':
    main()
