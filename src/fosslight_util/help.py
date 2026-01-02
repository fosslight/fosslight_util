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


# ANSI color codes for beautiful gradient effect
if _supports_color():
    _RESET = "\033[0m"
    _BOLD = "\033[1m"
    # Gradient colors with better visual impact
    _C1 = "\033[1;38;5;51m"   # Bright Cyan
    _C2 = "\033[1;38;5;45m"   # Turquoise
    _C3 = "\033[1;38;5;39m"   # Sky Blue
    _C4 = "\033[1;38;5;33m"   # Blue
    _C5 = "\033[1;38;5;27m"   # Deep Blue
    _C6 = "\033[1;38;5;21m"   # Dark Blue
    _STAR = "\033[1;38;5;226m" # Bright Yellow for stars
else:
    # No color support
    _RESET = _BOLD = _C1 = _C2 = _C3 = _C4 = _C5 = _C6 = _STAR = ""

_HELP_MESSAGE_COMMON = f"""
{_STAR}    ════════════════════════════════════════════════════════════════════{_RESET}
{_C1}    ███████╗ ██████╗ ███████╗ ███████╗{_C2}██╗     ██╗ ██████╗ ██╗  ██╗████████╗{_RESET}
{_C1}    ██╔════╝██╔═══██╗██╔════╝ ██╔════╝{_C2}██║     ██║██╔════╝ ██║  ██║╚══██╔══╝{_RESET}
{_C2}    █████╗  ██║   ██║███████╗ ███████╗{_C3}██║     ██║██║  ███╗███████║   ██║   {_RESET}
{_C3}    ██╔══╝  ██║   ██║╚════██║ ╚════██║{_C4}██║     ██║██║   ██║██╔══██║   ██║   {_RESET}
{_C4}    ██║     ╚██████╔╝███████║ ███████║{_C5}███████╗██║╚██████╔╝██║  ██║   ██║   {_RESET}
{_C5}    ╚═╝      ╚═════╝ ╚══════╝ ╚══════╝{_C6}╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   {_RESET}
{_STAR}    ════════════════════════════════════════════════════════════════════{_RESET}
{_STAR}                ✨ Open Source Analysis Tool ✨{_RESET}
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
