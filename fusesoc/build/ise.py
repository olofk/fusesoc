import os.path
import shutil
import subprocess
from fusesoc import utils

from fusesoc.build.backend import Backend
class Ise(Backend):

    TCL_FILE_TEMPLATE = """

project new {design}
project set family {family}
project set device {device}
project set package {package}
project set speed {speed}
project set "Generate Detailed MAP Report" true
project set "Verilog Include Directories" "{verilog_include_dirs}" -process "Synthesize - XST"
{source_files}
project set top "{top_module}"
"""

    TCL_FUNCTIONS = """
process run "Generate Programming File"
"""

    PGM_FILE_TEMPLATE = """
# Batch script for programming the device using a JTAG interface.
# Used with:
# $ impact -batch {pgm_file}

setMode -bscan
setCable -port auto
addDevice -p 1 -file {bit_file}
program -p 1
saveCDF -file {cdf_file}
quit
"""


    TOOL_NAME = 'ise'

    def __init__(self, system):
        super(Ise, self).__init__(system)
        self.work_root = os.path.join(self.build_root, 'bld-'+self.TOOL_NAME)

    def configure(self, args):
        super(Ise, self).configure(args)
        self._write_tcl_file()

    def _write_tcl_file(self):
        (src_files, incdirs) = self._get_fileset_files(['synth', 'ise'])
        ucf_files = [os.path.join(self.src_root, self.system.name, f.name) for f in self.system.backend.ucf_files]
        tcl_file = open(os.path.join(self.work_root, self.system.name+'.tcl'),'w')
        tcl_file.write(self.TCL_FILE_TEMPLATE.format(
            design               = self.system.name,
            family               = self.system.backend.family,
            device               = self.system.backend.device,
            package              = self.system.backend.package,
            speed                = self.system.backend.speed,
            top_module           = self.system.backend.top_module,
            verilog_include_dirs = '|'.join(incdirs),
            source_files = '\n'.join(['xfile add '+s.name for s in src_files] +
                                     ['xfile add '+s      for s in ucf_files])))
        if self.vlogparam:
            s = 'project set "Generics, Parameters" "{}" -process "Synthesize - XST"\n'
            tcl_file.write(s.format('|'.join([k+'='+str(v) for k,v in self.vlogparam.items()])))
        for f in self.system.backend.tcl_files:
            tcl_file.write(open(os.path.join(self.system_root, f.name)).read())

        tcl_file.write(self.TCL_FUNCTIONS)
        tcl_file.close()

    def build(self, args):
        super(Ise, self).build(args)

        utils.Launcher('xtclsh', [os.path.join(self.work_root, self.system.name+'.tcl')],
                           cwd = self.work_root,
                           errormsg = "Failed to make FPGA load module").run()
        super(Ise, self).done()

    def pgm(self, remaining):
        pgm_file_name = os.path.join(self.work_root, self.system.name+'.pgm')
        self._write_pgm_file(pgm_file_name)
        utils.Launcher('impact', ['-batch', pgm_file_name],
                           cwd = self.work_root,
                           errormsg = "impact tool returned an error").run()

    def _write_pgm_file(self, pgm_file_name):
        pgm_file = open(pgm_file_name,'w')
        pgm_file.write(self.PGM_FILE_TEMPLATE.format(
            pgm_file             = pgm_file_name,
            bit_file             = os.path.join(self.work_root, self.system.backend.top_module+'.bit'),
            cdf_file             = os.path.join(self.work_root, self.system.backend.top_module+'.cdf')))
        pgm_file.close()
