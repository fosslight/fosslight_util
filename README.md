<!--
Copyright (c) 2021 LG Electronics
SPDX-License-Identifier: Apache-2.0
 -->
 # FOSSLight Util

<img src="https://img.shields.io/pypi/l/fosslight_util" alt="FOSSLight Util is released under the Apache-2.0." /> <img src="https://img.shields.io/pypi/v/fosslight_util" alt="Current python package version." /> <img src="https://img.shields.io/pypi/pyversions/fosslight_util" /> [![REUSE status](https://api.reuse.software/badge/github.com/fosslight/fosslight_util)](https://api.reuse.software/info/github.com/fosslight/fosslight_util)

It is a package that supports common utils used by FOSSLight Scanner.

## Features 
1. It simplifies the logger setup.
2. It provides a simple function to create a output file.
3. It provides a spdx license list with json format.
4. It defines common constant variables.
5. It provides a thread that prints the spinner.
6. Download source code.

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
# 5th param : package name of fosslight scanners (fosslight_source / fosslight_dependency / fosslight_reuse)
# 6th param : path to analyze
#
# 1st return value : a logger
# 2nd return value : log items to print

def test():
    logger, log_item = init_log("test_result/log_file1.txt", True, 30, 20)
    logger.warning("TESTING - Print log")
```

  
### 2. Write result files (tests/test_output_format.py)
```
from fosslight_util.output_format import write_output_file

# 2nd param : output file format
#            => file format(excel: .xlsx, csv: .csv, opossum: .json)
def test():
    sheet_contents = {'SRC':[['run_scancode.py', 'fosslight_source',
                        '3.0.6', 'Apache-2.0',  'https://github.com/LGE-OSS/fosslight_source', 'https://github.com/LGE-OSS/fosslight_source', 'Copyright (c) 2021 LG Electronics, Inc.', 'Exclude', 'Comment message'],
                       ['dependency_unified.py', 'fosslight_dependency',
                        '3.0.6', 'Apache-2.0',  'https://github.com/LGE-OSS/fosslight_dependency', 'https://github.com/LGE-OSS/fosslight_dependency', 'Copyright (c) 2020 LG Electronics, Inc.', '', '']],
                      'BIN':[['askalono.exe', 'askalono',
                        '0.4.3', 'Apache-2.0', 'https://github.com/jpeddicord/askalono', '', 'Copyright (c) 2018 Amazon.com, Inc. or its affiliates.', '', '']]}
    success, msg = write_output_file('test_result/excel/FOSSLight-Report', '.xlsx', sheet_contents)
```
  
### 3. Get spdx licenses (tests/test_spdx_licenses.py)
```
from fosslight_util.spdx_licenses import get_spdx_licenses_json


def test():
    success, error_msg, licenses = get_spdx_licenses_json()
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

### 6. Download the source code (tests/test_download.py)
If you give a link, the source is downloaded to the target directory through git clone or wget.

#### How it works
1. Try git clone.
2. If git clone fails, download it with wget and extract the compressed file.
3. After extracting the compressed file, delete the compressed file.

#### Parameters      
| Parameter  | Argument | Description |
| ------------- | ------------- | ------------- |
| h | None | Print help message. | 
| s | String | Link to download. | 
| t | String | Path to download and extract. |
| d | String | Path to save a log file. | 

#### How to run
```
$ fosslight_download  -s "https://github.com/LGE-OSS/example" -t target_dir/
```

## 👏 How to report issue

Please report any ideas or bugs to improve by creating an issue in [fosslight_util repository][cl]. Then there will be quick bug fixes and upgrades. Ideas to improve are always welcome.

[cl]: https://github.com/fosslight/fosslight_util/issues

## 📄 License

FOSSLight Util is released under [Apache-2.0][l].

[l]: https://github.com/fosslight/fosslight_util/blob/main/LICENSE
