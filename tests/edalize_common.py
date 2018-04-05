import os.path

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
    defs = []
    for paramtype in paramtypes:
        for datatype in ['bool', 'int', 'str']:
            _arg = '--{}_{}'.format(paramtype, datatype)
            if datatype == 'int':
                _arg += '=42'
            elif datatype == 'str':
                _arg += '=hello'
            args.append(_arg)
            defs.append({'datatype'    : datatype,
                         'default'     : '',
                         'description' : '',
                         'name'        : paramtype+'_'+datatype,
                     'paramtype'   : paramtype})
    return (defs, args)

files = [
    {'name' : 'qip_file.qip' , 'file_type' : 'QIP'},
    {'name' : 'bmm_file'     , 'file_type' : 'BMM'},
    {'name' : 'sv_file.sv'   , 'file_type' : 'systemVerilogSource'},
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
    {'name' : 'xcd_file.xcd' , 'file_type' : 'xcd'}
]

vpi = [
    {'src_files': ['../src/vpi_0/f1',
                   '../src/vpi_0/f3'],
     'include_dirs': ['../src/vpi_0/'],
     'libs': ['some_lib'],
     'name': 'vpi1'},
    {'src_files': ['../src/vpi_0/f4'],
     'include_dirs': [],
     'libs': [],
     'name': 'vpi2'}]
    
