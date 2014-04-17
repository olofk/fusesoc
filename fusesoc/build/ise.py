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
project set "Verilog Include Directories" "{verilog_include_dirs}" -process "Synthesize - XST"
{source_files}
project set top "{top_module}"
"""

    TCL_FUNCTIONS = """
process run "Generate Programming File"
"""

    TOOL_NAME = 'ise'

    def __init__(self, system):
        super(Ise, self).__init__(system)
        self.src_files    += [os.path.join(self.src_root, self.system.name, f) for f in self.system.backend.ucf_files]
        self.work_root = os.path.join(self.build_root, 'bld-'+self.TOOL_NAME)

    def configure(self):
        super(Ise, self).configure()
        src_dir = self.system.system_root
        dst_dir = os.path.join(self.src_root, self.system.name)

        export_files = self.system.backend.export()
        dirs = list(set(map(os.path.dirname, export_files)))

        for d in dirs:
            if not os.path.exists(os.path.join(dst_dir, d)):
                os.makedirs(os.path.join(dst_dir, d))

        for f in export_files:
            if(os.path.exists(os.path.join(src_dir, f))):
                shutil.copyfile(os.path.join(src_dir, f),
                                os.path.join(dst_dir, f))
            else:
                pr_warn("File " + os.path.join(src_dir, f) + " doesn't exist")

        self._write_tcl_file()

    def _write_tcl_file(self):
        tcl_file = open(os.path.join(self.work_root, self.system.name+'.tcl'),'w')
        tcl_file.write(self.TCL_FILE_TEMPLATE.format(
            design               = self.system.name,
            family               = self.system.backend.family,
            device               = self.system.backend.device,
            package              = self.system.backend.package,
            speed                = self.system.backend.speed,
            top_module           = self.system.backend.top_module,
            verilog_include_dirs = '|'.join(self.include_dirs),
            source_files = '\n'.join(['xfile add '+s for s in self.src_files])))

        for f in self.system.backend.tcl_files:
            tcl_file.write(open(os.path.join(self.system_root, f)).read())

        tcl_file.write(self.TCL_FUNCTIONS)
        tcl_file.close()

    def build(self, args):
        super(Ise, self).build(args)

        utils.Launcher('xtclsh', [os.path.join(self.work_root, self.system.name+'.tcl')],
                           cwd = self.work_root,
                           errormsg = "Failed to make FPGA load module").run()
        super(Ise, self).done()

    def pgm(self, remaining):
        pass
