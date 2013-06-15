import shutil
import subprocess
from orpsoc.config import Config
from orpsoc.coremanager import CoreManager
import logging

logger = logging.getLogger(__name__)

class Backend(object):

    def __init__(self, system):
        logger.debug('__init__() *Entered*')
        config = Config()
        self.system = system
        self.build_root = os.path.join(config.build_root, self.system.name)
        self.systems_root = config.systems_root

        self.src_root = os.path.join(self.build_root, 'src')

        self.include_dirs = []
        self.src_files = []
        self.cm = CoreManager()

        self.cores = self.cm.get_depends(self.system.name)
        for core_name in self.cores:
            logger.debug('core_name=' + core_name)
            core = self.cm.get_core(core_name)
            if core.verilog:
                if core.verilog.include_dirs:
                    logger.debug('core.include_dirs=' + str(core.verilog.include_dirs))
                else:
                    logger.debug('core.include_dirs=None')
                self.include_dirs += [os.path.join(self.src_root, core_name, d) for d in core.verilog.include_dirs]
                self.src_files    += [os.path.join(self.src_root, core_name, f) for f in core.verilog.src_files]
        logger.debug('__init__() -Done-')

    def configure(self):
        logger.debug('configure() *Entered*')
        if os.path.exists(self.work_root): 
            shutil.rmtree(self.work_root)
        os.makedirs(self.work_root)
        cm = CoreManager()
        for name in self.cores:
            print("Preparing " + name)
            core = cm.get_core(name)
            dst_dir = os.path.join(Config().build_root, self.system.name, 'src', name)
            core.setup()
            core.export(dst_dir)
        logger.debug('configure() -Done-')

    def build(self):
        pass

import os

class Quartus(Backend):
#FIXME: Add proper credit to Stefan

    MAKEFILE_TEMPLATE = """

all: sta

project: $(TCL_FILE)
	quartus_sh -t $(DESIGN_NAME).tcl

map: project
	quartus_map $(DESIGN_NAME)

fit: map
	quartus_fit $(DESIGN_NAME)

asm: fit
	quartus_asm $(DESIGN_NAME)

sta: asm
	quartus_sta $(DESIGN_NAME)

clean:
	rm -rf *.* db incremental_db
"""

    TOOL_NAME = 'quartus'
    def __init__(self, system):
        logger.debug('Quartus __init__() *Entered*')
        super(Quartus, self).__init__(system)
        self.work_root = os.path.join(self.build_root, 'bld-'+self.TOOL_NAME)
        logger.debug('Quartus __init__() -Done-')

    def configure(self):
        logger.debug('configure() *Entered*')

        super(Quartus, self).configure()
        self._write_tcl_file()
        self._write_makefile()
        logger.debug('configure() -Done-')

    def _write_tcl_file(self):
        logger.debug('_write_tcl_file() *Entered*')
        tcl_file = open(os.path.join(self.work_root, self.system.name+'.tcl'),'w')
        tcl_file.write("project_new " + self.system.name + " -overwrite\n")
        tcl_file.write("set_global_assignment -name FAMILY " + self.system.backend['family'] + '\n')
        tcl_file.write("set_global_assignment -name DEVICE " + self.system.backend['device'] + '\n')
        tcl_file.write("set_global_assignment -name TOP_LEVEL_ENTITY " + "orpsoc_top" + '\n')
        for src_file in self.src_files:
            tcl_file.write("set_global_assignment -name VERILOG_FILE " + src_file + '\n')
        for include_dir in self.include_dirs:
            tcl_file.write("set_global_assignment -name SEARCH_PATH " + include_dir + '\n')

        #FIXME: Handle multiple SDC files. Also handle SDC files directly from cores?
        sdc_files = self.system.backend['sdc_files'].split()

        for f in sdc_files:
            src_file = os.path.join(self.systems_root, self.system.name, f)
            dst_file =os.path.join(self.work_root, f)
            if not os.path.exists(os.path.dirname(dst_file)):
                os.makedirs(os.path.dirname(dst_file))
            shutil.copyfile(src_file, dst_file)
            tcl_file.write("set_global_assignment -name SDC_FILE " + dst_file + '\n')

        tcl_files = self.system.backend['tcl_files'].split()
        for f in tcl_files:
            tcl_file.write(open(os.path.join(self.systems_root, self.system.name, f)).read())
        tcl_file.close()
        logger.debug('_write_tcl_file() -Done-')

    def _write_makefile(self):
        logger.debug('_write_makefile() *Entered*')
        makefile = open(os.path.join(self.work_root, 'Makefile'),'w')
        makefile.write("DESIGN_NAME = " + self.system.name)
        makefile.write(self.MAKEFILE_TEMPLATE)
        makefile.close()
        logger.debug('_write_makefile() -Done-')

    def build(self):
        logger.debug('build() *Entered*')
        # TODO: call super if necessary
        if subprocess.call("make",
                           cwd = self.work_root,
                           stdin=subprocess.PIPE):
            print("Error: Failed to make FPGA load module")
        # TODO: Check results, and report SUCCESS or FAILURE
        logger.debug('build() -Done-')



def BackendFactory(system):
    logger.debug('BackendFactory() *Entered*')
    #FIXME: Notify user if backend is missing from system description
    if system.backend_name == 'quartus':
        return Quartus(system)
    else:
        raise Exception("Backend not found")
