import os

class Section(object):
    def __init__(self):
        self.name = ""
        self.strings = []
        self.lists  = []

    def _add_listitem(self, listitem):
        self.lists += [listitem]
        setattr(self, listitem, [])

    def _add_stringitem(self, s):
        self.strings += [s]
        setattr(self, s, "")

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
