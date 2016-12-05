import os
from fusesoc.config import Config
from fusesoc import utils
from fusesoc.utils import pr_warn, pr_info, unique_dirs
from fusesoc.vlnv import Vlnv

class File(object):
    FILE_TYPES = [
        'QIP',
        'SDC',
        'tclSource',
        'user',
        'verilogSource',
        'verilogSource-95',
        'verilogSource-2001',
        'verilogSource-2005',
        'systemVerilogSource',
        'systemVerilogSource-3.0',
        'systemVerilogSource-3.1',
        'systemVerilogSource-3.1a',
        'vhdlSource',
        'vhdlSource-87',
        'vhdlSource-93',
        'vhdlSource-2008',
        'xci',
        'xdc',
        ]
    name      = ""
    file_type = ""
    is_include_file = False
    logical_name = ""
    def __init__(self, s):
        self.is_include_file = False
        if s[-1:] == ']':
            _tmp = s[:-1].split('[')
            if(len(_tmp) != 2):
                raise SyntaxError("Expected '['")
            self.name = _tmp[0]
            for _arg in [x.strip() for x in _tmp[1].split(',')]:
                if _arg == "is_include_file":
                    self.is_include_file = True
                elif '=' in _arg:
                    _tmp = [x.strip() for x in _arg.split('=')]
                    if _tmp[0] == 'file_type' and _tmp[1] not in self.FILE_TYPES:
                        _s = "Unknown file type '{}'. Allowed file types are {}"
                        raise SyntaxError(_s.format(_tmp[1], ', '.join(self.FILE_TYPES)))
                    if _tmp[0] in ['file_type', 'logical_name']:
                        setattr(self, _tmp[0], _tmp[1])
                else:
                    raise SyntaxError("Unexpected argument '"+_arg+"'")
        else:
            self.name = s

class Error(Exception):
    pass


class NoSuchItemError(Error):
    pass


class UnknownSection(Error):
    pass

class StringList(list):
    def __new__(cls, *args, **kwargs):
        if not args:
            return list()
        else:
            return list(args[0].split())

class PathList(StringList):
    def __new__(cls, *args, **kwargs):
        if not args:
            return list()
        else:
            return [os.path.expandvars(p) for p in args[0].split()]

class FileList(PathList):
    def __new__(clk, *args, **kwargs):
        if not args:
            return list()
        else:
            return [File(p) for p in PathList(args[0])]

class VlnvList(StringList):
    def __new__(clk, *args, **kwargs):
        if not args:
            return list()
        else:
            return [Vlnv(p) for p in StringList(args[0])]

class EnumList(list):
    def __new__(cls, *args, **kwargs):
        if not args:
            return super(EnumList, cls).__new__(cls)
        else:
            values = kwargs['values']
            _args = args[0].split()
            _valid = []
            _invalid = []
            for arg in _args:
                if arg in values:
                    _valid.append(arg)
                else:
                    _invalid.append(arg)
            if _invalid:
                raise ValueError(' '.join(_valid), _invalid, values)
            return _valid

class SimulatorList(EnumList):
    def __new__(cls, *args, **kwargs):
        values = ['ghdl', 'icarus', 'modelsim', 'verilator', 'isim', 'xsim']
        return super(SimulatorList, cls).__new__(cls, *args, values=values)

class SourceType(str):
    def __new__(cls, *args, **kwargs):
        if args:
            arg = args[0]
            values = ['C', 'CPP', 'systemC']
            if arg in values:
                return str(arg)
            raise ValueError("Invalid value '" + str(arg) + "'. Allowed values are '" + "', '".join(values)+"'")
        return str

class Section(object):

    TAG = None
    named = False
    def __init__(self):
        self._members = {}
        self.export_files = []
        self.warnings = []

    def _add_member(self, name, _type, desc):
        self._members[name] = {'type' : _type, 'desc' : desc}
        setattr(self, name, _type())

    def export(self):
        return self.export_files

    def load_dict(self, items):
        for item in items:
            if item in self._members:
                _type = self._members.get(item)['type']
                try:
                    setattr(self, item, _type(items.get(item)))
                except ValueError as e:
                    _s = "Invalid value '{}'. Allowed values are '{}'"
                    pr_warn(_s.format(', '.join(e.args[1]),
                                      ', '.join(e.args[2])))
                    setattr(self, item, _type(e.args[0]))
            else:
                self.warnings.append(
                        'Unknown item "%(item)s" in section "%(section)s"' % {
                            'item': item, 'section': self.TAG})

    def __str__(self):
        s = ''
        for k,v in self._members.items():
            if isinstance(v.get('type'), list):
                s += k + ' : ' + ';'.join(getattr(self, item)) + '\n'
            elif isinstance(v.get('type'), str):
                s += k + ' : ' + getattr(self, k) + '\n'
        return s

class ScriptsSection(Section):
    TAG = 'scripts'
    def __init__(self, items=None):
        super(ScriptsSection, self).__init__()
        self._add_member('pre_synth_scripts', StringList, 'Scripts to run before backend synthesis')
        self._add_member('post_impl_scripts', StringList, 'Scripts to run after backend implementation')
        self._add_member('pre_run_scripts'  , StringList, 'Scripts to run before running simulations')
        self._add_member('pre_build_scripts', StringList, 'Scripts to run before building')
        self._add_member('pre_run_scripts'  , StringList, 'Scripts to run before running simulations')
        self._add_member('post_run_scripts' , StringList, 'Scripts to run after simulations')

        if items:
            self.load_dict(items)

class ToolSection(Section):
    def __init__(self):
        super(ToolSection, self).__init__()
        self._add_member('depend', VlnvList, "Tool-specific Dependencies")
    def __str__(self):
        s = ""
        if self.depend:
            _s = "{}-specific dependencies : {}\n"
            s += _s.format(self.TAG,
                     ' '.join([x.depstr() for x in self.depend]))
        return(s)

class MainSection(Section):
    TAG = 'main'

    def __init__(self, items=None):
        super(MainSection, self).__init__()

        self._add_member('name'       , str     , "Component name")
        self._add_member('backend'    , str     , "Backend for FPGA implementation")
        self._add_member('component'  , PathList, "Core IP-Xact component file")
        self._add_member('description', str, "Core description")
        self._add_member('depend'     , VlnvList, "Common dependencies")
        self._add_member('simulators' , SimulatorList, "Supported simulators. Valid values are icarus, modelsim, verilator, isim and xsim. Each simulator have a dedicated section desribed elsewhere in this document")
        self._add_member('patches'    , StringList, "FuseSoC-specific patches")

        if items:
            self.load_dict(items)

class VhdlSection(Section):

    TAG = 'vhdl'

    def __init__(self, items=None):
        super(VhdlSection, self).__init__()

        self._add_member('src_files', PathList, "VHDL source files for simulation and synthesis")

        if items:
            self.load_dict(items)
            self.export_files = self.src_files

class VerilogSection(Section):

    TAG = 'verilog'

    def __init__(self, items=None):
        super(VerilogSection, self).__init__()

        self.include_dirs = []
        self.tb_include_dirs = []

        self._add_member('src_files'           , FileList, "Verilog source files for synthesis/simulation")
        self._add_member('include_files'       , FileList, "Verilog include files")
        self._add_member('tb_src_files'        , FileList, "Verilog source files that are only used in simulation. Visible to other cores")
        self._add_member('tb_private_src_files', FileList, "Verilog source files that are only used in the core's own testbench. Not visible to other cores")
        self._add_member('tb_include_files'    , FileList, "Testbench include files")
        self._add_member('file_type'           , str     , "Default file type of the files in fileset")

        if items:
            self.load_dict(items)
            if not self.file_type:
                self.file_type = "verilogSource"
            if self.include_files:
                self.include_dirs  += utils.unique_dirs(self.include_files)
            if self.tb_include_files:
                self.tb_include_dirs  += utils.unique_dirs(self.tb_include_files)

            self.export_files = self.src_files + self.include_files + self.tb_src_files + self.tb_include_files + self.tb_private_src_files

class FileSetSection(Section):
    TAG = 'fileset'
    named = True
    def __init__(self, items=None):
        super(FileSetSection, self).__init__()

        self._add_member('files'          , FileList, "List of files in fileset")
        self._add_member('file_type'      , str     , "Default file type of the files in fileset")
        self._add_member('is_include_file', str     , "Specify all files in fileset as include files")
        self._add_member('logical_name'   , str     , "Default logical_name (e.g. library) of the files in fileset")
        self._add_member('scope'          , str     , "Visibility of fileset (private/public). Private filesets are only visible when this core is the top-level. Public filesets are visible also for cores that depend on this core. Default is public")
        self._add_member('usage'          , StringList, "List of tags describing when this fileset should be used. Can be general such as sim or synth, or tool-specific such as quartus, verilator, icarus. Defaults to 'sim synth'.")
        if items:
            self.load_dict(items)
            if not self.scope:
                self.scope = 'public'
            if not self.usage:
                self.usage = ['sim', 'synth']
            for f in self.files:
                if not f.file_type:
                    f.file_type = self.file_type
                if self.is_include_file.lower() == "true":
                    f.is_include_file = True
                if not f.logical_name:
                    f.logical_name = self.logical_name
            self.export_files = self.files


class VpiSection(Section):

    TAG = 'vpi'

    def __init__(self, items=None):
        super(VpiSection, self).__init__()

        self.include_dirs = []

        self._add_member('src_files'    , FileList, "C source files for VPI library")
        self._add_member('include_files', FileList, "C include files for VPI library")
        self._add_member('libs'         , StringList, "External libraries linked with the VPI library")

        if items:
            self.load_dict(items)
            if self.include_files:
                self.include_dirs  += unique_dirs(self.include_files)

            self.export_files = self.src_files + self.include_files


class ModelsimSection(ToolSection):

    TAG = 'modelsim'

    def __init__(self, items=None):
        super(ModelsimSection, self).__init__()

        self._add_member('vlog_options', StringList, "Additional arguments for vlog")
        self._add_member('vsim_options', StringList, "Additional arguments for vsim")

        if items:
            self.load_dict(items)

class RivieraproSection(ToolSection):

    TAG = 'rivierapro'

    def __init__(self, items=None):
        super(RivieraproSection, self).__init__()

        self._add_member('vlog_options', StringList, "Additional arguments for vlog")
        self._add_member('vsim_options', StringList, "Additional arguments for vsim")

        if items:
            self.load_dict(items)

class GhdlSection(ToolSection):
    TAG = 'ghdl'

    def __init__(self, items=None):
        super(GhdlSection, self).__init__()

        self._add_member('analyze_options', StringList, "Extra GHDL analyzer options")
        self._add_member('run_options', StringList, "Extra GHDL run options")

        if items:
            self.load_dict(items)

    def __str__(self):
        s = super(GhdlSection, self).__str__()
        if self.analyze_options: s += "Extra GHDL analyzer options : {}\n".format(' '.join(self.analyze_options))
        if self.run_options: s += "Extra GHDL run options : {}\n".format(' '.join(self.run_options))
        return s

class IcarusSection(ToolSection):

    TAG = 'icarus'

    def __init__(self, items=None):
        super(IcarusSection, self).__init__()

        self._add_member('iverilog_options', StringList, "Extra Icarus verilog compile options")

        if items:
            self.load_dict(items)

    def __str__(self):
        s = super(IcarusSection, self).__str__()
        if self.iverilog_options: s += "Icarus compile options : {}\n".format(' '.join(self.iverilog_options))
        return s


class IsimSection(ToolSection):

    TAG = 'isim'

    def __init__(self, items=None):
        super(IsimSection, self).__init__()

        self._add_member('isim_options', StringList, "Extra Isim compile options")

        if items:
            self.load_dict(items)

    def __str__(self):
        s = super(IsimSection, self).__str__()
        if self.isim_options: s += "Isim compile options : {}\n".format(' '.join(self.isim_options))
        return s


class XsimSection(ToolSection):

    TAG = 'xsim'

    def __init__(self, items=None):
        super(XsimSection, self).__init__()

        self._add_member('xsim_options', StringList, "Extra Xsim compile options")

        if items:
            self.load_dict(items)

    def __str__(self):
        s = super(XsimSection, self).__str__()
        if self.xsim_options: s += "Xsim compile options : {}\n".format(' '.join(self.xsim_options))
        return s

class VerilatorSection(ToolSection):

    TAG = 'verilator'

    def __init__(self, items=None):
        super(VerilatorSection, self).__init__()

        self.include_dirs = []
        self.archive = False
        self._object_files = []

        self._add_member('verilator_options', StringList, "Verilator build options")
        self._add_member('src_files'        , FileList  , "Verilator testbench C/cpp/sysC source files")
        self._add_member('include_files'    , FileList  , "Verilator testbench C include files")
        self._add_member('define_files'     , PathList  , "Verilog include files containing `define directives to be converted to C #define directives in corresponding .h files")
        self._add_member('libs'             , PathList  , "External libraries linked with the generated model")

        self._add_member('tb_toplevel', str, 'Testbench top-level C/C++/SC file')
        self._add_member('source_type', str, 'Testbench source code language (Legal values are systemC, C, CPP. Default is C)')
        self._add_member('top_module' , str, 'verilog top-level module')
        self._add_member('cli_parser' , str, "Select CLI argument parser. Set to 'fusesoc' to handle parameter sections like other simulators. Set to 'passthrough' to send the arguments directly to the verilated model. Default is 'passthrough'")

        if items:
            self.load_dict(items)
            self.include_dirs  = unique_dirs(self.include_files)
            if self.src_files:
                self._object_files = [os.path.splitext(os.path.basename(s.name))[0]+'.o' for s in self.src_files]
                self.archive = True
                self.export_files = self.src_files + self.include_files


    def __str__(self):
        s = super(VerilatorSection, self).__str__()
        s += """Verilator options       : {verilator_options}
Testbench source files  : {src_files}
Testbench include files : {include_files}
Testbench define files  : {define_files}
External libraries      : {libs}
Testbench top level     : {tb_toplevel}
Testbench source type   : {source_type}
Verilog top module      : {top_module}
"""
        return s.format(verilator_options=' '.join(self.verilator_options),
                        src_files = ' '.join([f.name for f in self.src_files]),
                        include_files=' '.join([f.name for f in self.include_files]),
                        define_files=' '.join(self.define_files),
                        libs=' '.join(self.libs),
                        tb_toplevel=self.tb_toplevel,
                        source_type=self.source_type,
                        top_module=self.top_module)

class IcestormSection(ToolSection):

    TAG = 'icestorm'

    def __init__(self, items=None):
        super(IcestormSection, self).__init__()

        self._add_member('arachne_pnr_options', StringList, "arachne-pnr options")
        self._add_member('pcf_file' , FileList, "Physical constraint file")
        self._add_member('top_module', str, 'RTL top-level module')

        if items:
            self.load_dict(items)
            self.export_files = self.pcf_file

class VivadoSection(ToolSection):

    TAG = 'vivado'

    def __init__(self, items=None):
        super(VivadoSection, self).__init__()

        self._add_member('part'       , str, 'FPGA device part')
        self._add_member('hw_device'  , str, 'FPGA device identifier')
        self._add_member('top_module' , str, 'RTL top-level module')

        if items:
            self.load_dict(items)

class IseSection(ToolSection):

    TAG = 'ise'

    def __init__(self, items=None):
        super(IseSection, self).__init__()

        self._add_member('ucf_files' , FileList, "UCF constraint files")
        self._add_member('tcl_files' , FileList, "Extra TCL scripts")
        self._add_member('family'    , str, 'FPGA device family')
        self._add_member('device'    , str, 'FPGA device identifier')
        self._add_member('package'   , str, 'FPGA device package')
        self._add_member('speed'     , str, 'FPGA device speed grade')
        self._add_member('top_module', str, 'RTL top-level module')

        if items:
            self.load_dict(items)
            self.export_files = self.ucf_files

class QuartusSection(ToolSection):

    TAG = 'quartus'

    def __init__(self, items=None):
        super(QuartusSection, self).__init__()

        self._add_member('qsys_files', FileList, "Qsys IP description files")
        self._add_member('sdc_files' , FileList, "SDC constraint files")
        self._add_member('tcl_files' , FileList, "Extra script files")

        self._add_member('quartus_options', str, 'Quartus command-line options')
        self._add_member('family'         , str, 'FPGA device family')
        self._add_member('device'         , str, 'FPGA device identifier')
        self._add_member('top_module'     , str, 'RTL top-level module')

        if items:
            self.load_dict(items)
            self.export_files = self.qsys_files + self.sdc_files

class ParameterSection(Section):
    TAG = 'parameter'
    named = True
    def __init__(self, items=None):
        super(ParameterSection, self).__init__()

        self._add_member('datatype'   , str, 'Data type of argument (int, str, bool, file')
        self._add_member('default'    , str, 'Default value of argument')
        self._add_member('description', str, 'Parameter description')
        self._add_member('paramtype'  , str, 'Type of parameter (plusarg, vlogparam, generic, cmdlinearg')
        self._add_member('scope'      , str, 'Visibility of parameter. Private parameters are only visible when this core is the top-level. Public parameters are visible also when this core is pulled in as a dependency of another core')

        if items:
            self.load_dict(items)

def load_section(config, section_name, file_name='<unknown>'):
    tmp = section_name.split(' ')
    _type = tmp[0]
    if len(tmp) == 2:
        _name = tmp[1]
    else:
        _name = None
    cls = SECTION_MAP.get(_type)
    if cls is None:
        #Note: The following sections are not in section.py yet
        if not section_name in ['plusargs', 'simulator', 'provider']:
            pr_warn("Unknown section '{}' in '{}'".format(section_name, file_name))
        return None

    items = config.get_section(section_name)
    section = cls(items)
    if section.warnings:
        for warning in section.warnings:
            pr_warn('Warning: %s in %s' % (warning, file_name))
    if _name:
        return (section, _name)
    else:
        return section


def load_all(config, file_name='<unknown>'):
    for section_name in config.sections():
        section = load_section(config, section_name, file_name)
        if section:
            yield section


SECTION_MAP = {}


def _register_subclasses(parent):
    for cls in parent.__subclasses__():
        _register_subclasses(cls)
        if cls.TAG is None:
            continue
        SECTION_MAP[cls.TAG] = cls


_register_subclasses(Section)

if __name__ == "__main__":
    typenames = {str           : 'String',
                 FileList      : 'Space-separated list of files',
                 PathList      : 'Space-separated list of paths',
                 SimulatorList : 'Space-separated list',
                 SourceType    : 'String',
                 StringList    : 'Space-separated list',
                 VlnvList      : 'Space-separated list of VLNV identifiers',
                 list : 'List'}
    SECTION_TEMPLATE = """
{}
{}

[cols="2,1,5",options="header"]
|==============================
|Name | Type | Description
{}
|==============================

"""

    for k,v in sorted(SECTION_MAP.items()):
        c = v()
        s="\n".join(["|{} | {} | {}".format(k2, typenames[v2['type']], v2['desc']) for k2, v2 in sorted(c._members.items())])
        print(SECTION_TEMPLATE.format(k, '-'*len(k), s))
