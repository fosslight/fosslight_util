import os

import pytest
from fosslight_util.download import cli_download_and_extract

# legacy/test_download

def test_download_from_github():
    #when
    target_dir = "test_result/download/example"
    success, msg, _, _ = cli_download_and_extract("https://github.com/LGE-OSS/example",
                                                  target_dir,
                                                  "test_result/download_log/example")

    #then
    assert success is True
    assert len(os.listdir(target_dir)) > 0

@pytest.mark.parametrize("project_name, project_url",
                         [("filelock", "https://pypi.org/project/filelock/3.4.1"),
                          ("dependency", "https://pypi.org/project/fosslight-dependency/3.0.5/"),
                          ("jackson", "https://mvnrepository.com/artifact/com.fasterxml.jackson.core/jackson-databind/2.12.2"),
                          ("pub", "https://pub.dev/packages/file/versions/5.2.1")])
def test_download_from_wget(project_name, project_url):
    #given
    target_dir = "test_result/download/" + project_name
    log_dir = "test_result/download_log/" + project_name

    #when
    success, msg, _, _ = cli_download_and_extract(project_url, target_dir, log_dir)

    #then
    assert success is True
    assert len(os.listdir(target_dir)) > 0
