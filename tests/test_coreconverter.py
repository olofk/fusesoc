# TODO: probably https://gitlab.com/Rtzq0/structurediff should be used

import os.path

import pytest

tests_dir = os.path.dirname(__file__)
capi1_dir = os.path.join(tests_dir, "test_coreconverter", "capi1")
capi2_dir = os.path.join(tests_dir, "test_coreconverter", "capi2")
output_dir = os.path.join(tests_dir, "test_coreconverter", "capi2_converted")


def test_coreconverter():
    import filecmp

    from fusesoc.coreconverter import convert_core

    for filename in os.listdir(capi1_dir):
        if filename.endswith(".core"):
            input_filename = os.path.join(capi1_dir, filename)
            reference_filename = os.path.join(capi2_dir, filename)
            output_filename = os.path.join(output_dir, filename)

            convert_core(input_filename, output_filename)
            assert filecmp.cmp(reference_filename, output_filename)

            os.remove(output_filename)
