import os
from fosslight_util.convert_excel_to_yaml import convert_excel_to_yaml

def test_convert_excel_to_yaml():
    #given
    output_dir = "test_result/convert"
    output_yaml = os.path.join(os.path.abspath(output_dir), "fosslight-sbom-info")

    #when
    convert_excel_to_yaml("FOSSLight-Report_sample.xlsx", "test_result/convert/fosslight-sbom-info")

    #then
    assert len(os.listdir(output_dir)) > 0
