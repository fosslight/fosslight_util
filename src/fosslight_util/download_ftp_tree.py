import ftplib
import os
import re
import logging
import fosslight_util.constant as constant
from pathlib import Path

"""
MIT license: 2017 - Jwely
Example usage:
``` python
import ftplib
ftp = ftplib.FTP(mysite, username, password)
download_ftp_tree(ftp, remote_dir, local_dir)
```
The code above will look for a directory called "remote_dir" on the ftp host, and then duplicate the
directory and its entire contents into the "local_dir".
*** Note that if wget is an option, I recommend using that instead ***
"""
logger = logging.getLogger(constant.LOGGER_NAME)


def _is_ftp_dir(ftp_handle, name, guess_by_extension=True):
    """ simply determines if an item listed on the ftp server is a valid directory or not """

    # if the name has a "." in the fourth to last position, its probably a file extension
    # this is MUCH faster than trying to set every file to a working directory, and will work 99% of time.
    if guess_by_extension is True:
        if len(name) >= 4:
            if name[-4] == '.':
                return False

    original_cwd = ftp_handle.pwd()  # remember the current working directory
    try:
        ftp_handle.cwd(name)  # try to set directory to new name
        ftp_handle.cwd(original_cwd)  # set it back to what it was
        return True

    except ftplib.error_perm as e:
        print(e)
        return False

    except Exception as e:
        print(e)
        return False


def _make_parent_dir(fpath):
    """ ensures the parent directory of a filepath exists """
    dirname = os.path.dirname(fpath)
    while not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
            print("created {0}".format(dirname))
        except OSError as e:
            print(e)
            _make_parent_dir(dirname)


def _download_ftp_file(ftp_handle, name, dest, overwrite):
    """ downloads a single file from an ftp server """
    _make_parent_dir(dest.lstrip("/"))
    if not os.path.exists(dest) or overwrite is True:
        try:
            with open(dest, 'wb') as f:
                ftp_handle.retrbinary("RETR {0}".format(name), f.write)
            print("downloaded: {0}".format(dest))
        except FileNotFoundError:
            print("FAILED: {0}".format(dest))
    else:
        print("already exists: {0}".format(dest))


def _file_name_match_patern(pattern, name):
    """ returns True if filename matches the pattern"""
    if pattern is None:
        return True
    else:
        return bool(re.match(pattern, name))


def _mirror_ftp_dir(ftp_handle, name, overwrite, guess_by_extension, pattern):
    """ replicates a directory on an ftp server recursively """
    for item in ftp_handle.nlst(name):
        if _is_ftp_dir(ftp_handle, item, guess_by_extension):
            _mirror_ftp_dir(ftp_handle, item, overwrite, guess_by_extension, pattern)
        else:
            if _file_name_match_patern(pattern, name):
                _download_ftp_file(ftp_handle, item, item, overwrite)
            else:
                # quietly skip the file
                pass


def download_ftp_tree(ftp_handle, path, destination, pattern=None, overwrite=False, guess_by_extension=True):
    """
    Downloads an entire directory tree from an ftp server to the local destination
    :param ftp_handle: an authenticated ftplib.FTP instance
    :param path: the folder on the ftp server to download
    :param destination: the local directory to store the copied folder
    :param pattern: Python regex pattern, only files that match this pattern will be downloaded.
    :param overwrite: set to True to force re-download of all files, even if they appear to exist already
    :param guess_by_extension: It takes a while to explicitly check if every item is a directory or a file.
        if this flag is set to True, it will assume any file ending with a three character extension ".???" is
        a file and not a directory. Set to False if some folders may have a "." in their names -4th position.
    """
    success = True
    try:
        logger.warning("2222222222222222")
        path = path.lstrip("/")
        original_directory = os.getcwd()  # remember working directory before function is executed
        Path(destination).mkdir(parents=True, exist_ok=True)
        os.chdir(destination)  # change working directory to ftp mirror directory

        logger.warning("333333333333333")
        _mirror_ftp_dir(
            ftp_handle,
            path,
            pattern=pattern,
            overwrite=overwrite,
            guess_by_extension=guess_by_extension)

        logger.warning("4444444444444444")
        os.chdir(original_directory)  # reset working directory to what it was before function exec
    except Exception as ex:
        success = False
        logger.info(f"Error downloading ftp tree: {ex}")

    return success
