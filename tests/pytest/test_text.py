import os
from fosslight_util.write_txt import write_txt_file

def test_text():
    #given
    output_dir = "test_result/txt"
    file_to_create = os.path.join(output_dir, "test.txt")
    text_to_write = "Testing - Writing text in a file."

    #when
    success, error_msg = write_txt_file(file_to_create, text_to_write)
    with open(file_to_create, 'r', encoding='utf-8') as result_file:
        result = result_file.read()

    #then
    assert success is True
    assert text_to_write in result

