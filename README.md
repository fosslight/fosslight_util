<!--
Copyright (c) 2021 LG Electronics
SPDX-License-Identifier: Apache-2.0
 -->
 # FOSSLight Util

<img src="https://img.shields.io/pypi/l/fosslight_util" alt="FOSSLight Util is released under the Apache-2.0." /> <img src="https://img.shields.io/pypi/v/fosslight_util" alt="Current python package version." /> <img src="https://img.shields.io/pypi/pyversions/fosslight_util" /> [![REUSE status](https://api.reuse.software/badge/github.com/fosslight/fosslight_util)](https://api.reuse.software/info/github.com/fosslight/fosslight_util)

It is a package that supports common utils used by FOSSLight Scanner.

## Features 
1. It simplifies the logger setup.
2. It easily outputs csv file and excel file in FOSSLight Report format.
3. It provides a simple function to create a text file.
4. It defines common constant variables.
5. It provides a thread that prints the spinner.

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
from fosslight_util.set_log import init_log

# 1st param : log file path
# 2nd param : create file (True/False)
# 3rd param : stream log level
# 4th param : file log level
#            =>log level(CRITICAL:50, ERROR:40, WARNING:30, INFO:20, DEBUG:10, NOTSET:0)

def test():
    logger = init_log("test_result/log_file1.txt", True, 30, 20)
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
        'test_result/excel/FOSSLight-Report', sheet_contents)
```
  
### 3. Write a text file (tests/test_text.py)
```
from fosslight_util.write_txt import write_txt_file


def test():
    success, error_msg = write_txt_file("test_result/txt/test.txt",
                                       "Testing - Writing text in a file.")
```

### 4. Load common constant (tests/_print_log_with_another_logger.py)
```
import fosslight_util.constant as constant


logger = logging.getLogger(constant.LOGGER_NAME)
logger.warning("Get a logger after init_log is called once.")
```

### 5. Call a spinner (tests/test_timer.py)
```
from fosslight_util.timer_thread import TimerThread


timer = TimerThread()
timer.setDaemon(True)
timer.start()
```

## 👏 How to report issue

Please report any ideas or bugs to improve by creating an issue in [fosslight_util repository][cl]. Then there will be quick bug fixes and upgrades. Ideas to improve are always welcome.

[cl]: https://github.com/fosslight/fosslight_util/issues

## 📄 License

FOSSLight Util is released under [Apache-2.0][l].

[l]: https://github.com/fosslight/fosslight_util/blob/main/LICENSE
