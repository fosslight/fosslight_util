<p align="center">
  <strong>FOSSLight Util</strong><br>
  Combine all the logs & Print result as csv and excel
</p>

<p align="center">
    <img src="https://img.shields.io/badge/license-LGE-orange.svg" alt="FOSSLight Scanner is released under the LGE Proprietary License." />
    <img src="https://img.shields.io/badge/pypi-v0.1-brightgreen.svg" alt="Current python package version." />
    <img src="https://img.shields.io/badge/python-3.6+-blue.svg" />
</p>

**FOSSLight Util** 
1. It simplifies the logger setup.
2. It easily outputs csv file and excel file in [OSS Report][or] format.
3. It provides a simple function to create a text file.

[or]: http://collab.lge.com/main/x/xDHlFg

## Contents

- [Prerequisite](#-prerequisite)
- [How to install](#-how-to-install)
- [How to run](#-how-to-run)
- [How to report issue](#-how-to-report-issue)
- [License](#-license)


## 📋 Prerequisite

FOSSLight Reporter needs a Python 3.6+.

## 🎉 How to install

It can be installed using pip3. 

```
$ pip3 install "http://mod.lge.com/code/rest/archive/latest/projects/OSC/repos/fosslight_reporter/archive?format=zip" 
```

## 🚀 How to use

Three modules can be called. Please refer to each file for detailed calling method.

   
### 1. Setup logger (tests/test_log.py)
```
from fosslight_reporter._set_log import init_log


def test():
    logger = init_log("test_result/log_file1.txt")
    logger.warning("TESTING - Print log")
```
  
### 2. Write csv and excel files (tests/test_excel.py)
```
from fosslight_reporter._write_excel import write_excel_and_csv


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
from fosslight_reporter.write_txt import write_txt_file


def test():
    success, error_msg = write_txt_file("test_result/txt/test.txt",
                                       "Testing - Writing text in a file.")
```
## 👏 How to report issue

Please report any ideas or bugs to improve by creating an issue in [OSC CLM][cl]. Then there will be quick bug fixes and upgrades. Ideas to improve are always welcome.

[cl]: http://clm.lge.com/issue/browse/OSC

## 📄 License

FOSSLight Source is LGE licensed, as found in the [LICENSE][l] file.

[l]: http://mod.lge.com/code/projects/OSC/repos/fosslight_reporter/browse/LICENSE
