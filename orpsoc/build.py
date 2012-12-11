import shutil
import subprocess
from orpsoc.config import Config

class Backend(object):

    def __init__(self, system):
        config = Config()
        self.system = system
        self.build_root = os.path.join(config.build_root, self.system.name)
        self.cores_root = config.cores_root
        self.systems_root = config.systems_root

        self.src_root = os.path.join(self.build_root, 'src')

        self.include_dirs = []
        self.src_files = []
        for core_name in self.system.get_cores():
            core = self.system.cores[core_name]
            self.include_dirs += [os.path.join(self.src_root, core_name, d) for d in core.verilog.include_dirs]
            self.src_files    += [os.path.join(self.src_root, core_name, f) for f in core.verilog.src_files]

    def configure(self):
        pass

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
        super(Quartus, self).__init__(system)
        self.work_root = os.path.join(self.build_root, 'bld-'+self.TOOL_NAME)

    def configure(self):
        if os.path.exists(self.work_root): # Move to Backend.configure?
            shutil.rmtree(self.work_root)
        os.makedirs(self.work_root)
        self._write_tcl_file()
        self._write_makefile()

    def _write_tcl_file(self):
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

    def _write_makefile(self):
        makefile = open(os.path.join(self.work_root, 'Makefile'),'w')
        makefile.write("DESIGN_NAME = " + self.system.name)
        makefile.write(self.MAKEFILE_TEMPLATE)
        makefile.close()

    def build(self):
        # TODO: call super if necessary
        if subprocess.call("make",
                           cwd = self.work_root,
                           stdin=subprocess.PIPE):
            print("Error: Failed to make FPGA load module")
        # TODO: Check results, and report SUCCESS or FAILURE

def BackendFactory(system):
    #FIXME: Notify user if backend is missing from system description
    if system.backend_name == 'quartus':
        return Quartus(system)
    else:
        raise Exception("Backend not found")
