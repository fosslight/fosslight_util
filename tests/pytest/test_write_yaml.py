import pytest
from fosslight_util.write_yaml import write_yaml

# legacy/test_yaml

def test_write_yaml(sheet_list_fixture_for_write_yaml):
    #given
    output_file1 = 'test_result/yaml/FL-TEST_yaml.yaml'
    output_file2 = 'test_result/yaml/FL-TEST2_yaml.yaml'
    sheet_list1 = sheet_list_fixture_for_write_yaml[0]
    sheet_list2 = sheet_list_fixture_for_write_yaml[1]

    #when
    success1, msg1, output1 = write_yaml(output_file1, sheet_list1)
    success2, msg2, output2 = write_yaml(output_file2, sheet_list2)

    #then
    assert success1 is True
    assert success2 is True
    assert output_file1 in output1
    assert output_file2 in output2
