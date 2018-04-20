import os
import shutil
import pytest

from test_common import get_core, build_root

tests_dir = os.path.dirname(__file__)
core      = get_core("wb_intercon")

def test_export():
    export_root = os.path.join(build_root, core.name.sanitized_name, 'src')

    for f in [
            'verilog_utils_0/verilog_utils.vh',
            'vlog_tb_utils_1.1/vlog_tap_generator.v',
            'vlog_tb_utils_1.1/vlog_tb_utils.v',
            'vlog_tb_utils_1.1/vlog_functions.v',
            'wb_intercon_1.0/dummy_icarus.v',
            'wb_intercon_1.0/bench/wb_mux_tb.v',
            'wb_intercon_1.0/bench/wb_upsizer_tb.v',
            'wb_intercon_1.0/bench/wb_intercon_tb.v',
            'wb_intercon_1.0/bench/wb_arbiter_tb.v',
            'wb_intercon_1.0/rtl/verilog/wb_data_resize.v',
            'wb_intercon_1.0/rtl/verilog/wb_mux.v',
            'wb_intercon_1.0/rtl/verilog/wb_arbiter.v',
            'wb_intercon_1.0/rtl/verilog/wb_upsizer.v',
            'verilog-arbiter_0-r1/src/arbiter.v',
            'wb_common_0/wb_common_params.v',
            'wb_common_0/wb_common.v']:
        assert os.path.isfile(os.path.join(export_root, f))
