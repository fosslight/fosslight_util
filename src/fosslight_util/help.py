#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import sys
import os
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError  # Python <3.8


def _supports_color():
    """Check if the terminal supports color."""
    # Check if output is redirected or if NO_COLOR environment variable is set
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False
    if os.environ.get('NO_COLOR'):
        return False
    # Windows cmd.exe support (Windows 10+)
    if sys.platform == 'win32':
        return True
    # Unix-like systems
    return True


if _supports_color():
    _RESET = "\033[0m"
    _BOLD = "\033[1m"
    _C1 = "\033[1;38;2;230;140;165m"  # Toned Down Light Pink
    _C2 = "\033[1;38;2;217;115;153m"  # Toned Down Pink
    _C3 = "\033[1;38;2;242;115;166m"  # Medium Light Pink
    _C4 = "\033[1;38;2;230;77;140m"   # Pink
    _C5 = "\033[1;38;2;217;38;115m"   # Pink-Red
    _C6 = "\033[1;38;2;191;19;89m"    # Medium Red
    _C7 = "\033[1;38;2;165;0;52m"     # Burgundy (#A50034) - Middle
    _C8 = "\033[1;38;2;140;0;44m"     # Dark Burgundy
    _C9 = "\033[1;38;2;115;0;36m"     # Darker Burgundy
    _C10 = "\033[1;38;2;89;0;28m"     # Very Dark Burgundy
    _STAR = "\033[1;38;5;226m"  # Bright Yellow for stars
else:
    # No color support
    _RESET = _BOLD = _C1 = _C2 = _C3 = _C4 = _C5 = _C6 = _C7 = _C8 = _C9 = _C10 = _STAR = ""

_HELP_MESSAGE_COMMON = f"""
{_STAR} ═════════════════════════════════════════════════════════════════════{_RESET}
{_C1} ███████╗ {_C1}██████╗ {_C2}███████╗ {_C2}███████╗{_C3}██╗     {_C3}██╗ {_C4}██████╗ {_C5}██╗  {_C5}██╗{_C6}████████╗{_RESET}
{_C1} ██╔════╝{_C2}██╔═══██╗{_C2}██╔════╝ {_C3}██╔════╝{_C3}██║     {_C4}██║{_C4}██╔════╝ {_C5}██║  {_C6}██║{_C6}╚══██╔══╝{_RESET}
{_C2} █████╗  {_C2}██║   ██║{_C3}███████╗ {_C3}███████╗{_C4}██║     {_C5}██║{_C5}██║  ███╗{_C6}███████║{_C7}   {_C7}██║   {_RESET}
{_C3} ██╔══╝  {_C3}██║   ██║{_C4}╚════██║ {_C4}╚════██║{_C5}██║     {_C6}██║{_C6}██║   ██║{_C7}██╔══██║{_C8}   {_C8}██║   {_RESET}
{_C3} ██║     {_C4}╚██████╔╝{_C5}███████║ {_C5}███████║{_C6}███████╗{_C7}██║{_C7}╚██████╔╝{_C8}██║  {_C9}██║   {_C9}██║   {_RESET}
{_C4} ╚═╝      {_C5}╚═════╝ {_C5}╚══════╝ {_C6}╚══════╝{_C7}╚══════╝{_C8}╚═╝ {_C8}╚═════╝ {_C9}╚═╝  {_C10}╚═╝ {_C10}╚═╝ {_RESET}
{_STAR} ═════════════════════════════════════════════════════════════════════{_RESET}
{_STAR}                   ✨ Open Source Analysis Tool ✨{_RESET}
"""


_HELP_MESSAGE_DOWNLOAD = """
    FOSSLight Downloader is a tool to download the package via input URL

    Usage: fosslight_download [option1] <arg1> [options2] <arg2>
     ex) fosslight_download -s http://github.com/fosslight/fosslight -t output_dir -d log_dir

    Required:
        -s\t\t      URL of the package to be downloaded

    Optional:
        -h\t\t      Print help message
        -t\t\t      Output path name
        -d\t\t      Directory name to save the log file
        -s\t\t      Source link to download
        -t\t\t      Directory to download source code
        -c\t\t      Checkout to branch or tag/ or version
        -z\t\t      Unzip only compressed file
        -o\t\t      Generate summary output file with this option"""


class PrintHelpMsg():

    def __init__(self, value: str = ""):
        self.message_suffix = value

    def print_help_msg(self, exitopt: bool) -> None:
        print(_HELP_MESSAGE_COMMON)
        print(self.message_suffix)

        if exitopt:
            sys.exit()


def print_package_version(pkg_name: str, msg: str = "", exitopt: bool = True) -> str:
    if msg == "":
        msg = f"{pkg_name} Version:"
    try:
        cur_version = version(pkg_name)
    except PackageNotFoundError:
        cur_version = "unknown"

    if exitopt:
        print(f'{msg} {cur_version}')
        sys.exit(0)
    else:
        return cur_version


def print_help_msg_download(exitOpt=True):
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_DOWNLOAD)
    helpMsg.print_help_msg(exitOpt)
