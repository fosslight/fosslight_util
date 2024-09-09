import os
from fosslight_util.download import cli_download_and_extract

def test_download_from_github():
    #when
    target_dir = "test_result/download/example"
    success, msg, _, _ = cli_download_and_extract("https://github.com/LGE-OSS/example",
                                                  target_dir,
                                                  "test_result/download_log/example")

    #then
    assert success is True
    assert len(os.listdir(target_dir)) > 0

def test_download_from_wget():
    #when
    target_dir = "test_result/download/filelock"
    success, msg, _, _ = cli_download_and_extract("https://pypi.org/project/filelock/3.4.1",
                                                  target_dir,
                                                  "test_result/download_log/filelock")

    #then
    assert success is True
    assert len(os.listdir(target_dir)) > 0
