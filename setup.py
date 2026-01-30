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
        version='2.1.39',
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
                     "Programming Language :: Python :: 3.10",
                     "Programming Language :: Python :: 3.11",
                     "Programming Language :: Python :: 3.12", ],
        install_requires=required,
        package_data={'fosslight_util': ['resources/frequentLicenselist.json', 'resources/licenses.json']},
        include_package_data=True,
        entry_points={
            "console_scripts": [
                "fosslight_download = fosslight_util.download:main",
            ]
        }
    )
