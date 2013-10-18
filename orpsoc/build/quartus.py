import os.path
import shutil
import subprocess

from orpsoc.build.backend import Backend
class Quartus(Backend):

    MAKEFILE_TEMPLATE = """

all: sta

project: $(TCL_FILE)
	quartus_sh $(QUARTUS_OPTIONS) -t $(DESIGN_NAME).tcl

map: project
	quartus_map $(QUARTUS_OPTIONS) $(DESIGN_NAME)

fit: map
	quartus_fit $(QUARTUS_OPTIONS) $(DESIGN_NAME)

asm: fit
	quartus_asm $(QUARTUS_OPTIONS) $(DESIGN_NAME)

sta: asm
	quartus_sta $(QUARTUS_OPTIONS) $(DESIGN_NAME)

clean:
	rm -rf *.* db incremental_db
"""

    TOOL_NAME = 'quartus'
    def __init__(self, system):
        super(Quartus, self).__init__(system)
        self.work_root = os.path.join(self.build_root, 'bld-'+self.TOOL_NAME)

    def configure(self):

        super(Quartus, self).configure()
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
        quartus_options = self.system.backend.get('quartus_options', '')
        makefile = open(os.path.join(self.work_root, 'Makefile'),'w')
        makefile.write("DESIGN_NAME = " + self.system.name + "\n")
        makefile.write("QUARTUS_OPTIONS = " + quartus_options + "\n")
        makefile.write(self.MAKEFILE_TEMPLATE)
        makefile.close()

    def build(self):
        # TODO: call super if necessary
        if subprocess.call("make",
                           cwd = self.work_root,
                           stdin=subprocess.PIPE):
            print("Error: Failed to make FPGA load module")
        # TODO: Check results, and report SUCCESS or FAILURE


    def pgm(self, remaining):
        args = ['--mode=jtag']
        args += remaining
        args += ['-o']
        args += ['p;' + self.system.name + '.sof']
        utils.launch('quartus_pgm', args, cwd=self.work_root)
