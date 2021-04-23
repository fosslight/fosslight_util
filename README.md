# FOSSLight Util

<img src="https://img.shields.io/badge/license-Apache--2.0-orange.svg" alt="FOSSLight Util is released under the Apache-2.0." /> <img src="https://img.shields.io/badge/pypi-v1.0-brightgreen.svg" alt="Current python package version." /> <img src="https://img.shields.io/badge/python-3.6+-blue.svg" />

It is a package that supports common utils used by FOSSLight Scanner.

## Features 
1. It simplifies the logger setup.
2. It easily outputs csv file and excel file in OSS Report format.
3. It provides a simple function to create a text file.

[or]: http://collab.lge.com/main/x/xDHlFg

## Contents

- [Prerequisite](#-prerequisite)
- [How to install](#-how-to-install)
- [How to run](#-how-to-run)
- [How to report issue](#-how-to-report-issue)
- [License](#-license)


## 📋 Prerequisite

FOSSLight Util needs a Python 3.6+.

## 🎉 How to install

It can be installed using pip3. 

```
$ pip3 install fosslight_util
```

## 🚀 How to use

Three modules can be called. Please refer to each file for detailed calling method.

   
### 1. Setup logger (tests/test_log.py)
```
from fosslight_util._set_log import init_log


def test():
    logger = init_log("test_result/log_file1.txt")
    logger.warning("TESTING - Print log")
```
  
### 2. Write csv and excel files (tests/test_excel.py)
```
from fosslight_util._write_excel import write_excel_and_csv


def test():
    sheet_contents = {'SRC':[['run_scancode.py', 'fosslight_source',
                        '3.0.6', 'Apache-2.0',  'https://github.com/LGE-OSS/fosslight_source', 'https://github.com/LGE-OSS/fosslight_source', 'Copyright (c) 2021 LG Electronics, Inc.', 'Exclude', 'Comment message'],
                       ['dependency_unified.py', 'fosslight_dependency',
                        '3.0.6', 'Apache-2.0',  'https://github.com/LGE-OSS/fosslight_dependency', 'https://github.com/LGE-OSS/fosslight_dependency', 'Copyright (c) 2020 LG Electronics, Inc.', '', '']],
                      'BIN':[['askalono.exe', 'askalono',
                        '0.4.3', 'Apache-2.0', 'https://github.com/jpeddicord/askalono', '', 'Copyright (c) 2018 Amazon.com, Inc. or its affiliates.', '', '']]}

    success, msg = write_excel_and_csv(
        'test_result/excel/OSS-Report', sheet_contents)
```
  
### 3. Write a text file (tests/test_text.py)
```
from fosslight_util.write_txt import write_txt_file


def test():
    success, error_msg = write_txt_file("test_result/txt/test.txt",
                                       "Testing - Writing text in a file.")
```
## 👏 How to report issue

Please report any ideas or bugs to improve by creating an issue in [fosslight_util repository][cl]. Then there will be quick bug fixes and upgrades. Ideas to improve are always welcome.

[cl]: https://github.com/fosslight/fosslight_util/issues

## 📄 License

FOSSLight Util is released under [Apache-2.0][l].

[l]: https://github.com/fosslight/fosslight_util/blob/main/LICENSE