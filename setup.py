#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics
# SPDX-License-Identifier: Apache-2.0
from codecs import open
from setuptools import setup, find_packages

with open('README.md', 'r', 'utf-8') as f:
    readme = f.read()

with open('requirements.txt', 'r', 'utf-8') as f:
    required = f.read().splitlines()

if __name__ == "__main__":
    setup(
        name='fosslight_util',
        version='1.4.19',
        package_dir={"": "src"},
        packages=find_packages(where='src'),
        description='FOSSLight Util',
        long_description=readme,
        long_description_content_type='text/markdown',
        license='Apache-2.0',
        author='LG Electronics',
        url='https://github.com/fosslight/fosslight_util',
        download_url='https://github.com/fosslight/fosslight_util',
        classifiers=['License :: OSI Approved :: Apache Software License',
                     "Programming Language :: Python :: 3",
                     "Programming Language :: Python :: 3.6",
                     "Programming Language :: Python :: 3.7",
                     "Programming Language :: Python :: 3.8",
                     "Programming Language :: Python :: 3.9", ],
        install_requires=required,
        package_data={'fosslight_util': ['resources/frequentLicenselist.json', 'resources/licenses.json']},
        include_package_data=True,
        extras_require={":python_version<'3.7'": ["pygit2==1.6.1"],
                        ":python_version>'3.6'": ["pygit2==1.10.1"]},
        entry_points={
            "console_scripts": [
                "fosslight_download = fosslight_util.download:main",
            ]
        }
    )
