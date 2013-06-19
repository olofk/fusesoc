import os
import logging

logger = logging.getLogger(__name__)

class Verilog:

    def __init__(self, items):
        logger.debug('__init__() *Entered*')
        logger.debug("  items=" + str(items))

        self.src_files = []
        self.include_files = []
        self.include_dirs = []

        self.tb_src_files = []
        self.tb_private_src_files = []
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
            elif item == 'tb_private_src_files':
                self.tb_private_src_files = items.get(item).split()
            elif item == 'tb_include_files':
                self.tb_include_files = items.get(item).split()
                self.tb_include_dirs  = list(set(map(os.path.dirname, self.tb_include_files)))
            else:
                print("Warning: Unknown item '" + item +"' in verilog section")
        logger.debug('__init__() -Done-')

    def export(self):
        logger.debug('export() *Entered*')
        self.export_files = self.src_files + self.include_files + self.tb_src_files + self.tb_include_files + self.tb_private_src_files
        logger.debug("  export_files="+str(self.export_files));
        return self.export_files
