import os
from fusesoc import utils
from fusesoc.utils import Launcher

class Section(object):
    def __init__(self):
        self.name = ""
        self.strings = []
        self.lists  = []
        self.export_files = []

    def _add_listitem(self, listitem):
        self.lists += [listitem]
        setattr(self, listitem, [])

    def _add_stringitem(self, s):
        self.strings += [s]
        setattr(self, s, "")

    def export(self):
        return self.export_files

    def load_dict(self, items):
        for item in items:
            if item in self.lists:
                setattr(self, item, items.get(item).split())
            elif item in self.strings:
                setattr(self, item, items.get(item))
            else:
                print("Warning: Unknown item '{item}' in section '{section}'".format(item=item, section=self.name))

    def __str__(self):
        s = ''
        for item in self.lists:
            s += item + ' : ' + ';'.join(getattr(self, item)) + '\n'
        for item in self.strings:
            s += item + ' : ' + getattr(self, item) + '\n'
        return s

    @staticmethod
    def factory(type, items=None):
        if type == 'icarus'    : return IcarusSection(items)
        if type == 'modelsim'  : return ModelsimSection(items)
        if type == 'verilator' : return VerilatorSection(items)
        if type == 'vhdl'      : return VhdlSection(items)
        if type == 'verilog'   : return VerilogSection(items)
        raise Exception

class VhdlSection(Section):
    def __init__(self, items=None):
        super(VhdlSection, self).__init__()

        self._add_listitem('src_files')

        if items:
            self.load_dict(items)
            self.export_files = self.src_files

class VerilogSection(Section):
    def __init__(self, items=None):
        super(VerilogSection, self).__init__()

        self.include_dirs = []
        self.tb_include_dirs = []

        self._add_listitem('src_files')
        self._add_listitem('include_files')
        self._add_listitem('tb_src_files')
        self._add_listitem('tb_private_src_files')
        self._add_listitem('tb_include_files')

        if items:
            self.load_dict(items)
            if self.include_files:
                self.include_dirs  += list(set(map(os.path.dirname, self.include_files)))
            if self.tb_include_files:
                self.tb_include_dirs  += list(set(map(os.path.dirname, self.tb_include_files)))

            self.export_files = self.src_files + self.include_files + self.tb_src_files + self.tb_include_files + self.tb_private_src_files

class ToolSection(Section):
    def __init__(self):
        super(ToolSection, self).__init__()
        self._add_listitem('depend')

class ModelsimSection(ToolSection):
    def __init__(self, items=None):
        super(ModelsimSection, self).__init__()
        
        self.name = 'modelsim'
        self._add_listitem('vlog_options')
        self._add_listitem('vsim_options')

        if items:
            self.load_dict(items)

class IcarusSection(ToolSection):
    def __init__(self, items=None):
        super(IcarusSection, self).__init__()

        self.name = 'icarus'
        self._add_listitem('iverilog_options')

        if items:
            self.load_dict(items)

class VerilatorSection(ToolSection):
    def __init__(self, items=None):
        super(VerilatorSection, self).__init__()

        self.name ='verilator'

        self.include_dirs = []
        self.archive = False
        self._object_files = []

        self._add_listitem('verilator_options')
        self._add_listitem('src_files')
        self._add_listitem('include_files')
        self._add_listitem('define_files')
        self._add_listitem('libs')
        
        self._add_stringitem('tb_toplevel')
        self._add_stringitem('source_type')
        self._add_stringitem('top_module')

        if items:
            self.load_dict(items)
            self.include_dirs  = list(set(map(os.path.dirname, self.include_files)))
            if self.src_files:
                self._object_files = [os.path.splitext(os.path.basename(s))[0]+'.o' for s in self.src_files]
                self.archive = True
                self.export_files = self.src_files + self.include_files


    def __str__(self):
        s = """Verilator options       : {verilator_options}
Testbench source files  : {src_files}
Testbench include files : {include_files}
Testbench define files  : {define_files}
External libraries      : {libs}
Testbench top level     : {tb_toplevel}
Testbench source type   : {source_type}
Verilog top module      : {top_module}
"""
        return s.format(verilator_options=' '.join(self.verilator_options),
                        src_files = ' '.join(self.src_files),
                        include_files=' '.join(self.include_files),
                        define_files=' '.join(self.define_files),
                        libs=' '.join(self.libs),
                        tb_toplevel=self.tb_toplevel,
                        source_type=self.source_type,
                        top_module=self.top_module)

    def build(self, core, sim_root, src_root):
        if self.source_type == 'C' or self.source_type == '':
            self.build_C(core, sim_root, src_root)
        elif self.source_type == 'CPP':
            self.build_CPP(core, sim_root, src_root)
        elif self.source_type == 'systemC':
            self.build_SysC(core, sim_root, src_root)
        else:
            raise Source(self.source_type)
        
        if self._object_files:
            args = []
            args += ['rvs']
            args += [core+'.a']
            args += self._object_files
            Launcher('ar', args,
                     cwd=sim_root).run()

    def build_C(self, core, sim_root, src_root):
        args = ['-c']
        args += ['-std=c99']
        args += ['-I'+src_root]
        args += ['-I'+os.path.join(src_root, core, s) for s in self.include_dirs]
        for src_file in self.src_files:
            print("Compiling " + src_file)
            l = Launcher('gcc',
                     args + [os.path.join(src_root, core, src_file)],
                     cwd=sim_root)
            print(l)
            l.run()

    def build_CPP(self, core, sim_root, src_root):
        verilator_root = utils.get_verilator_root()
        if verilator_root is None:
            verilator_root = utils.get_verilator_root()
        args = ['-c']
        args += ['-I'+src_root]
        args += ['-I'+os.path.join(src_root, core, s) for s in self.include_dirs]
        args += ['-I'+os.path.join(verilator_root,'include')]
        args += ['-I'+os.path.join(verilator_root,'include', 'vltstd')]
        for src_file in self.src_files:
            print("Compiling " + src_file)
            l = Launcher('g++', args + [os.path.join(src_root, core, src_file)],
                         cwd=sim_root)
            print(l)
            l.run()

    def build_SysC(self, core, sim_root, src_root):
        verilator_root = utils.get_verilator_root()
        args = ['-I.']
        args += ['-MMD']
        args += ['-I'+src_root]
        args += ['-I'+s for s in self.include_dirs]
        args += ['-Iobj_dir']
        args += ['-I'+os.path.join(verilator_root,'include')]
        args += ['-I'+os.path.join(verilator_root,'include', 'vltstd')]  
        args += ['-DVL_PRINTF=printf']
        args += ['-DVM_TRACE=1']
        args += ['-DVM_COVERAGE=0']
        args += ['-I'+os.getenv('SYSTEMC_INCLUDE')]
        args += ['-Wno-deprecated']
        if os.getenv('SYSTEMC_CXX_FLAGS'):
             args += [os.getenv('SYSTEMC_CXX_FLAGS')]
        args += ['-c']
        args += ['-g']

        for src_file in self.src_files:
            print("Compiling " + src_file)
            Launcher('g++',args + ['-o' + os.path.splitext(os.path.basename(src_file))[0]+'.o']+ [src_file],
                     cwd=sim_root).run()
        
