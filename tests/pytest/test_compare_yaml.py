import os
from fosslight_util.compare_yaml import compare_yaml

# legacy/test_compare_yaml

def test_compare_yaml(fixture_constants):
    #given
    before_yaml_file = os.path.join(fixture_constants["TEST_RESOURCES_DIR"], 'before.yaml')
    after_yaml_file = os.path.join(fixture_constants["TEST_RESOURCES_DIR"], 'after.yaml')

    #when
    result = compare_yaml(before_yaml_file, after_yaml_file)

    #then
    assert len(result["add"]) > 0;
    assert len(result["change"]) > 0;
    assert len(result["delete"]) > 0;

