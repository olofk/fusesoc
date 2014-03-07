import os
import logging

logger = logging.getLogger(__name__)

class VHDL:

    def __init__(self):
        self.src_files = []
        self.tb_src_files = []
        self.tb_private_src_files = []

    def load_items(self, items):
        logger.debug('__init__() *Entered*')
        logger.debug("  items=" + str(items))

        for item in items:
            if item == 'src_files':
                self.src_files = items.get(item).split()
            elif item == 'tb_src_files':
                self.tb_src_files = items.get(item).split()
            elif item == 'tb_private_src_files':
                self.tb_private_src_files = items.get(item).split()
            else:
                print("Warning: Unknown item '" + item +"' in vhdl section")
        logger.debug('__init__() -Done-')

    def export(self):
        logger.debug('export() *Entered*')
        self.export_files = self.src_files + self.tb_src_files + self.tb_private_src_files
        logger.debug("  export_files="+str(self.export_files));
        return self.export_files
