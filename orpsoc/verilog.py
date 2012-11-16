import os

class Verilog:
    def __init__(self, items):
        self.src_files = []
        self.include_files = []
        self.include_dirs = []

        self.tb_src_files = []
        self.tb_include_files = []
        self.tb_include_dirs = []

        for item in items:
            if item == 'src_files':
                self.src_files = items.get(item).split()
            elif item == 'include_files':
                self.include_files = items.get(item).split()
                self.include_dirs  = list(set(map(os.path.dirname, self.include_files)))
            elif item == 'tb_src_files':
                self.tb_src_files = items.get(item).split()
            elif item == 'tb_include_files':
                self.tb_include_files = items.get(item).split()
                self.tb_include_dirs  = list(set(map(os.path.dirname, self.tb_include_files)))
            else:
                print("Warning: Unknown item '" + item +"' in verilog section")

    def export(self):
        return self.src_files + self.include_files + self.tb_src_files + self.tb_include_files
