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

        self._add_listitem('verilator_options')
        self._add_listitem('src_files')
        self._add_listitem('include_files')
        self._add_listitem('define_files')
        self._add_listitem('libs')
        
        self._add_stringitem('tb_toplevel')
        self._add_stringitem('source_type')

        if items:
            self.load_dict(items)
            self.include_dirs  = list(set(map(os.path.dirname, self.include_files)))
