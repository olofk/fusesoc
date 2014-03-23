import os.path
import shutil
import subprocess
import argparse
from fusesoc import utils

from fusesoc.build.backend import Backend
class Ise(Backend):

    MAKEFILE_TEMPLATE = """

all: bitgen

xst:
	xst -ifn $(DESIGN_NAME).xst

ngdbuild: xst
	ngdbuild -uc $(DESIGN_NAME).ucf $(DESIGN_NAME).ngc

map: ngdbuild
	map -detail -ol high -w $(DESIGN_NAME).ngd

par: map
	par -ol high -w $(DESIGN_NAME).ncd $(DESIGN_NAME)-routed.ncd

bitgen: par
	bitgen -g LCK_cycle:6 -g Binary:Yes -w $(DESIGN_NAME)-routed.ncd $(DESIGN_NAME).bit

timingreport: $(DESIGN_NAME)-routed.ncd
	trce -u 1000 -e 1000 $< $(DESIGN_NAME).pcf

clean:
	rm -rf *.*
"""

    TOOL_NAME = 'ise'
    def __init__(self, system):
        super(Ise, self).__init__(system)
        self.work_root = os.path.join(self.build_root, 'bld-'+self.TOOL_NAME)

    def configure(self):

        super(Ise, self).configure()
        self._write_prj_file()
        self._write_ucf_file()
        self._write_xst_file()
        self._write_makefile()

    def _write_ucf_file(self):
        ucf_file = open(os.path.join(self.work_root,
                                     self.system.name+'.ucf'),'w')
        ucf_files = self.system.backend['ucf_files'].split()

        for f in ucf_files:
            src_filename = os.path.join(self.systems_root, self.system.name, f)
            with open(src_filename) as src_file:
                ucf_file.write(src_file.read())
        ucf_file.close();

    def _write_xst_file(self):
        xst_file = open(os.path.join(self.work_root,
                                     self.system.name+'.xst'),'w')
        xst_file_content = """
run
-ifn {design_name}.prj
-ifmt mixed
-top {top_module}
-ofmt NGC
-ofn {design_name}.ngc
-p {device}
-opt_level 2
-opt_mode Speed
-vlgincdir {{ {inc_dirs} }}
""".format(design_name = self.system.name,
           top_module = self.system.backend['top_module'],
           inc_dirs = ' '.join(self.include_dirs),
           device = self.system.backend['device'])

        print xst_file_content

        xst_file.write(xst_file_content)
        xst_file.close()

    def _write_prj_file(self):
        prj_file = open(os.path.join(self.work_root,
                                     self.system.name+'.prj'),'w')
        for src_file in self.src_files:
             prj_file.write("verilog work " + src_file + '\n')

    def _write_makefile(self):
        makefile = open(os.path.join(self.work_root, 'Makefile'),'w')
        makefile.write("DESIGN_NAME = " + self.system.name + "\n")
        makefile.write(self.MAKEFILE_TEMPLATE)
        makefile.close()

    def build(self, args):
        super(Ise, self).build(args)

        parser = argparse.ArgumentParser(prog="fusesoc build " +
                                         self.system.name,
                                         conflict_handler='resolve')

        parser.add_argument('--64-bit', action='store_true',
                            help="run backend in 64-bit mode")
        parser.add_argument('--ise_path',
                            help="path to ise (e.g. /opt/Xilinx/13.4)")
        p = parser.parse_args(args)

        # NOTE: 'if p.64_bit:' will not work since the arg starts with a number
        if vars(p)['64_bit']:
            bits = 64
        else:
            bits = 32

        if p.ise_path is None:
            # No specific path given, make an educated guess.
            ise_versions = [dir for dir in os.listdir("/opt/Xilinx/")]
            ise_path = "/opt/Xilinx/{0}/ISE_DS".format(max(ise_versions))
        else:
            ise_path = os.path.join(p.ise_path, "ISE_DS")

        ise_settings = os.path.join(ise_path, "settings{0}.sh".format(bits))

        if subprocess.call("source " + ise_settings + " && make",
                           cwd = self.work_root,
                           shell=True,
                           stdin=subprocess.PIPE):
            print("Error: Failed to make FPGA load module")

        super(Ise, self).done()
