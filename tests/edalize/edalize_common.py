import os.path
import tempfile

from edalize import get_edatool

tests_dir = os.path.dirname(__file__)

def compare_files(ref_dir, work_root, files):
    import os.path

    for f in files:
        reference_file = os.path.join(ref_dir, f)
        generated_file = os.path.join(work_root, f)

        assert os.path.exists(generated_file)

        with open(reference_file) as fref, open(generated_file) as fgen:
            assert fref.read() == fgen.read(), f

def param_gen(paramtypes):
    args = []
    defs = {}
    for paramtype in paramtypes:
        for datatype in ['bool', 'int', 'str']:
            _arg = '--{}_{}'.format(paramtype, datatype)
            if datatype == 'int':
                _arg += '=42'
            elif datatype == 'str':
                _arg += '=hello'
            args.append(_arg)
            defs[paramtype+'_'+datatype] = {
                'datatype'    : datatype,
                'description' : '',
                'paramtype'   : paramtype}
    return (defs, args)

def setup_backend_minimal(name, tool, files):
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']

    work_root = tempfile.mkdtemp(prefix=tool+'_')

    eda_api = {'name'         : name,
               'files'        : files,
               'toplevel'     : 'top_module',
    }
    return (get_edatool(tool)(eda_api=eda_api,
                              work_root=work_root), work_root)


def setup_backend(paramtypes, name, tool, tool_options, use_vpi=False):
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    (parameters, args) = param_gen(paramtypes)

    work_root = tempfile.mkdtemp(prefix=tool+'_')

    _vpi = []
    if use_vpi:
        _vpi = vpi
        for v in vpi:
            for f in v['src_files']:
                _f = os.path.join(work_root, f)
                if not os.path.exists(os.path.dirname(_f)):
                    os.makedirs(os.path.dirname(_f))
                with open(_f, 'a'):
                    os.utime(_f, None)

    eda_api = {'name'         : name,
               'files'        : files,
               'parameters'   : parameters,
               'tool_options' : {tool : tool_options},
               'toplevel'     : 'top_module',
               'vpi'          :  _vpi}

    backend = get_edatool(tool)(eda_api=eda_api, work_root=work_root)
    return (backend, args, work_root)

files = [
    {'name' : 'qip_file.qip' , 'file_type' : 'QIP'},
    {'name' : 'qsys_file'    , 'file_type' : 'QSYS'},
    {'name' : 'sdc_file'     , 'file_type' : 'SDC'},
    {'name' : 'bmm_file'     , 'file_type' : 'BMM'},
    {'name' : 'sv_file.sv'   , 'file_type' : 'systemVerilogSource'},
    {'name' : 'pcf_file.pcf' , 'file_type' : 'PCF'},
    {'name' : 'ucf_file.ucf' , 'file_type' : 'UCF'},
    {'name' : 'user_file'    , 'file_type' : 'user'},
    {'name' : 'tcl_file.tcl' , 'file_type' : 'tclSource'},
    {'name' : 'vlog_file.v'  , 'file_type' : 'verilogSource'},
    {'name' : 'vlog05_file.v', 'file_type' : 'verilogSource-2005'},
    {'name' : 'vlog_incfile' , 'file_type' : 'verilogSource', 'is_include_file' : True},
    {'name' : 'vhdl_file.vhd', 'file_type' : 'vhdlSource'},
    {'name' : 'vhdl_lfile'   , 'file_type' : 'vhdlSource', 'logical_name' : 'libx'},
    {'name' : 'vhdl2008_file', 'file_type' : 'vhdlSource-2008'},
    {'name' : 'xci_file.xci' , 'file_type' : 'xci'},
    {'name' : 'xdc_file.xdc' , 'file_type' : 'xdc'}
]

vpi = [
    {'src_files': ['src/vpi_1/f1',
                   'src/vpi_1/f3'],
     'include_dirs': ['src/vpi_1/'],
     'libs': ['some_lib'],
     'name': 'vpi1'},
    {'src_files': ['src/vpi_2/f4'],
     'include_dirs': [],
     'libs': [],
     'name': 'vpi2'}]
    
