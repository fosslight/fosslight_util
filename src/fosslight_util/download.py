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
import getopt
import shutil
import pygit2 as git
import bz2
from datetime import datetime
from pathlib import Path
from ._get_downloadable_url import get_downloadable_url
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
import signal
import time
import threading
import platform

logger = logging.getLogger(constant.LOGGER_NAME)
compression_extension = {".tar.bz2", ".tar.gz", ".tar.xz", ".tgz", ".tar", ".zip", ".jar", ".bz2"}
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
    pass


def alarm_handler(signum, frame):
    logger.warning("download timeout! (%d sec)", SIGNAL_TIMEOUT)
    raise TimeOutException()


def print_help_msg():
    print("* Required : -s link_to_download")
    print("* Optional : -t target_directory")
    print("* Optional : -d log_file_directory")
    sys.exit(0)


def main():

    src_link = ""
    target_dir = os.getcwd()
    log_dir = os.getcwd()

    try:
        argv = sys.argv[1:]
        opts, args = getopt.getopt(argv, 'hs:t:d:')
    except getopt.GetoptError:
        print_help_msg()

    for opt, arg in opts:
        if opt == "-h":
            print_help_msg()
        elif opt == "-s":
            src_link = arg
        elif opt == "-t":
            target_dir = arg
        elif opt == "-d":
            log_dir = arg

    if src_link == "":
        print_help_msg()
    else:
        cli_download_and_extract(src_link, target_dir, log_dir)


def cli_download_and_extract(link, target_dir, log_dir, checkout_to="", compressed_only=False):
    global logger

    success = True
    msg = ""
    log_file_name = "fosslight_download_" + \
        datetime.now().strftime('%Y%m%d_%H-%M-%S')+".txt"
    logger, log_item = init_log(os.path.join(log_dir, log_file_name))

    try:
        if link == "":
            success = False
            msg = "Need a link to download."
        elif os.path.isfile(target_dir):
            success = False
            msg = "The target directory exists as a file.:"+target_dir
        else:
            if not download_git_clone(link, target_dir, checkout_to):
                if os.path.isfile(target_dir):
                    shutil.rmtree(target_dir)

                success, downloaded_file = download_wget(link, target_dir, compressed_only)
                if success:
                    success = extract_compressed_file(downloaded_file, target_dir, True)
    except Exception as error:
        success = False
        msg = str(error)

    logger.info("* FOSSLight Downloader - Result :"+str(success)+"\n"+msg)
    return success, msg


def get_ref_to_checkout(checkout_to, ref_list):
    ref_to_checkout = checkout_to
    try:
        checkout_to = checkout_to.strip()
        if checkout_to in ref_list:
            return checkout_to

        prefix_refs = ["refs/remotes/origin/", "refs/tags/"]
        for prefix in prefix_refs:
            ref_to_checkout = prefix+checkout_to
            if ref_to_checkout in ref_list:
                return ref_to_checkout

        ref_to_checkout = next(
            x for x in ref_list if x.endswith(checkout_to))
    except Exception as error:
        logger.warning("git find ref - failed:"+str(error))
    return ref_to_checkout


def download_git_clone(git_url, target_dir, checkout_to=""):
    if platform.system() != "Windows":
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(SIGNAL_TIMEOUT)
    else:
        alarm = Alarm(SIGNAL_TIMEOUT)
        alarm.start()
    try:
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        repo = git.clone_repository(git_url, target_dir,
                                    bare=False, repository=None,
                                    remote=None, callbacks=None)
        if platform.system() != "Windows":
            signal.alarm(0)
        else:
            del alarm
    except Exception as error:
        logger.warning("git clone - failed:"+str(error))
        return False
    try:
        ref_to_checkout = checkout_to
        if checkout_to != "":
            ref_list = [x for x in repo.references]
            ref_to_checkout = get_ref_to_checkout(checkout_to, ref_list)
            logger.info("git checkout :"+ref_to_checkout)
            repo.checkout(ref_to_checkout)
    except Exception as error:
        logger.warning("git checkout to "+ref_to_checkout +
                       " - failed:"+str(error))
    return True


def download_wget(link, target_dir, compressed_only):
    success = False
    downloaded_file = ""
    if platform.system() != "Windows":
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(SIGNAL_TIMEOUT)
    else:
        alarm = Alarm(SIGNAL_TIMEOUT)
        alarm.start()
    try:
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        ret, new_link = get_downloadable_url(link)
        if ret and new_link != "":
            link = new_link

        if compressed_only:
            for ext in compression_extension:
                if link.endswith(ext):
                    success = True
                    break
        else:
            success = True

        if not success:
            raise Exception('Not supported compression type (link:{0})'.format(link))

        logger.info("wget:"+link)
        downloaded_file = wget.download(link)
        if platform.system() != "Windows":
            signal.alarm(0)
        else:
            del alarm

        shutil.move(downloaded_file, target_dir)
        downloaded_file = os.path.join(target_dir, downloaded_file)
        if downloaded_file != "":
            success = True
            logger.debug("wget - downloaded:"+downloaded_file)
    except Exception as error:
        success = False
        logger.warning("wget - failed:"+str(error))

    return success, downloaded_file


def extract_compressed_dir(src_dir, target_dir, remove_after_extract=True):
    logger.debug("Extract Dir:"+src_dir)
    try:
        files_path = [os.path.join(src_dir, x) for x in os.listdir(src_dir)]
        for fname in files_path:
            extract_compressed_file(fname, target_dir, remove_after_extract)
    except Exception as error:
        logger.debug("Extract files in dir - failed:"+str(error))
        return False
    return True


def extract_compressed_file(fname, extract_path, remove_after_extract=True):
    try:
        is_compressed_file = True
        if os.path.isfile(fname):
            if fname.endswith(".tar.bz2"):
                decompress_bz2(fname, extract_path)
                os.remove(fname)
                fname = os.path.splitext(fname)[0]

            if fname.endswith(".tar.gz") or fname.endswith(".tgz"):
                tar = tarfile.open(fname, "r:gz")
                tar.extractall(path=extract_path)
                tar.close()
            elif fname.endswith(".tar.xz") or fname.endswith(".tar"):
                tar = tarfile.open(fname, "r:*")
                tar.extractall(path=extract_path)
                tar.close()
            elif fname.endswith(".zip") or fname.endswith(".jar"):
                unzip(fname, extract_path)
            elif fname.endswith(".bz2"):
                decompress_bz2(fname, extract_path)
            else:
                is_compressed_file = False
                logger.warning("Unsupported file extension:"+fname)

            if remove_after_extract and is_compressed_file:
                logger.debug("Remove - extracted file :"+fname)
                os.remove(fname)
        else:
            logger.warning("Not a file:"+fname)
    except Exception as error:
        logger.error("Extract - failed:"+str(error))
        return False
    return True


def decompress_bz2(source_file, dest_path):
    try:
        fzip = bz2.BZ2File(source_file)
        data = fzip.read()  # get the decompressed data
        open(os.path.splitext(source_file)[0], 'wb').write(data)  # write a uncompressed file

    except Exception as error:
        logger.error("Decompress bz2 - failed:"+str(error))
        return False
    return True


def unzip(source_file, dest_path):
    try:
        fzip = zipfile.ZipFile(source_file, 'r')
        for filename in fzip.namelist():
            fzip.extract(filename, dest_path)
        fzip.close()
    except Exception as error:
        logger.error("Unzip - failed:"+str(error))
        return False
    return True


if __name__ == '__main__':
    main()
