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
    _C1 = "\033[1;38;5;218m"   # Light Pink
    _C2 = "\033[1;38;5;211m"   # Pink
    _C3 = "\033[1;38;5;212m"   # Medium Light Pink
    _C4 = "\033[1;38;5;205m"   # Pink
    _C5 = "\033[1;38;5;198m"   # Pink-Red
    _C6 = "\033[1;38;5;161m"   # Medium Red
    _C7 = "\033[1;38;5;125m"   # Burgundy - Middle
    _C8 = "\033[1;38;5;88m"    # Dark Burgundy
    _C9 = "\033[1;38;5;52m"    # Darker Burgundy
    _C10 = "\033[1;38;5;53m"   # Very Dark Burgundy
    _STAR = "\033[1;38;5;226m"  # Bright Yellow for stars
else:
    # No color support
    _RESET = _C1 = _C2 = _C3 = _C4 = _C5 = _C6 = _C7 = _C8 = _C9 = _C10 = _STAR = ""

_HELP_MESSAGE_COMMON = f"""
{_STAR} ═════════════════════════════════════════════════════════════════════{_RESET}
{_C1} ███████╗ {_C1}██████╗ {_C2}███████╗ {_C2}███████╗{_C3}██╗     {_C3}██╗ {_C4}██████╗ {_C5}██╗  {_C5}██╗{_C6}████████╗{_RESET}
{_C1} ██╔════╝{_C2}██╔═══██╗{_C2}██╔════╝ {_C3}██╔════╝{_C3}██║     {_C4}██║{_C4}██╔════╝ {_C5}██║  {_C6}██║{_C6}╚══██╔══╝{_RESET}
{_C2} █████╗  {_C2}██║   ██║{_C3}███████╗ {_C3}███████╗{_C4}██║     {_C5}██║{_C5}██║  ███╗{_C6}███████║{_C7}   {_C7}██║   {_RESET}
{_C3} ██╔══╝  {_C3}██║   ██║{_C4}╚════██║ {_C4}╚════██║{_C5}██║     {_C6}██║{_C6}██║   ██║{_C7}██╔══██║{_C8}   {_C8}██║   {_RESET}
{_C3} ██║     {_C4}╚██████╔╝{_C5}███████║ {_C5}███████║{_C6}███████╗{_C7}██║{_C7}╚██████╔╝{_C8}██║  {_C9}██║   {_C9}██║   {_RESET}
{_C4} ╚═╝      {_C5}╚═════╝ {_C5}╚══════╝ {_C6}╚══════╝{_C7}╚══════╝{_C8}╚═╝ {_C8}╚═════╝ {_C9}╚═╝  {_C10}╚═╝   {_C10}╚═╝ {_RESET}
{_STAR} ═════════════════════════════════════════════════════════════════════{_RESET}
{_STAR}                   ✨ Open Source Analysis Tool ✨{_RESET}
"""


_HELP_MESSAGE_DOWNLOAD = """
    📖 Usage
    ────────────────────────────────────────────────────────────────────
    fosslight_download [options] <arguments>

    📝 Description
    ────────────────────────────────────────────────────────────────────
    FOSSLight Downloader is a tool to download a package or source code from a given URL.

    ⚙️  General Options
    ────────────────────────────────────────────────────────────────────
    -s <url>              URL of the package or source to download (required)
    -t <path>             Output directory to save the downloaded files
    -d <log_dir>          Directory to save the log file
    -c <branch/tag>       Checkout to branch, tag, or version after download
    -l <GB>               Max download size in GB (omit for unlimited)
    -z                    Unzip only compressed file
    -o                    Generate summary output file
    -h                    Show this help message

    💡 Examples
    ────────────────────────────────────────────────────────────────────
    # Download a GitHub repository to output_dir and save log
    fosslight_download -s https://github.com/fosslight/fosslight -t output_dir -d log_dir

    # Download and checkout to a specific branch
    fosslight_download -s https://github.com/fosslight/fosslight -t output_dir -c develop

    # Limit download size to 3 GB
    fosslight_download -s https://github.com/fosslight/fosslight -t output_dir -l 3

    # Download and unzip a compressed file
    fosslight_download -s https://example.com/archive.zip -z -t output_dir
"""


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
