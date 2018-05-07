import pytest

def test_copyto():
    import os
    import tempfile

    from fusesoc.vlnv import Vlnv

    from test_common import common_cm

    flags = {'tool' : 'icarus'}

    work_root = tempfile.mkdtemp(prefix='copyto_')

    eda_api = common_cm.setup(Vlnv("copytocore"), flags, work_root, None)

    assert eda_api['files'] == [{'file_type': 'user',
                                 'logical_name': '',
                                 'name': 'copied.file',
                                 'is_include_file': False},
                                {'file_type': 'tclSource',
                                 'logical_name': '',
                                 'name': 'subdir/another.file',
                                 'is_include_file': False}]
    assert os.path.exists(os.path.join(work_root, 'copied.file'))
    assert os.path.exists(os.path.join(work_root, 'subdir', 'another.file'))

def test_export():
    import os
    import tempfile

    from fusesoc.vlnv import Vlnv

    from test_common import common_cm

    tests_dir = os.path.dirname(__file__)
    build_root = tempfile.mkdtemp(prefix='export_')
    export_root = os.path.join(build_root, 'exported_files')
    eda_api = common_cm.setup(Vlnv("::wb_intercon:1.0"),
                       {'tool' : 'icarus'},
                       work_root=os.path.join(build_root, 'work'),
                       export_root=export_root)

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
