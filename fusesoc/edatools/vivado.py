import os.path
import platform
from fusesoc import utils

from fusesoc.edatool import EdaTool

tool_options = {'members' : {'part' : 'String'}}

""" Vivado Backend

The Vivado backend executes Xilinx Vivado to build systems and program the FPGA.

The backend defines the following section:

    [vivado]
    part = <part name> # Format <family><device><package>-<speedgrade>
    hw_device = <device name> # Format <family><device>_0
    top_module = <RTL module name>

A core (usually the system core) can add the following files:

- Standard design sources

- Constraints: Supply xdc files with file_type=xdc

- IP: Supply the IP core xci file with file_type=xci and other files (like .prj)
      as file_type=data
"""
class Vivado(EdaTool):

    argtypes = ['vlogdefine', 'vlogparam']

    """ Configuration is the first phase of the build

    In the vivado backend the project TCL is written and all files are copied
    """
    def configure_main(self):
        if not 'part' in self.tool_options:
            raise RuntimeError("Missing required option '{}'".format('part'))
        self._write_project_tcl_file()

    """ Write the project TCL file

    This writes the project TCL file. It first collects all sources, IPs and
    contraints and then writes them to the TCL file along with the build steps.
    """
    def _write_project_tcl_file(self):
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        template_vars = {}
        template_vars['name'] = self.name
        template_vars['src_files'] = src_files
        template_vars['incdirs'] = incdirs
        template_vars['tool_options'] = self.tool_options
        template_vars['bitstream_name'] = self.name+'.bit'
        template_vars['toplevel'] = self.toplevel
        template_vars['vlogparam'] = self.vlogparam
        template_vars['vlogdefine'] = self.vlogdefine
        prj_file_path = os.path.join(self.work_root, self.name+".tcl")
        template = self.jinja_env.get_template('vivado/vivado-project.tcl.j2')
        with open(prj_file_path, 'w') as prj_file:
            prj_file.write(template.render(template_vars))

    """ Execute the build

    This launches the actual build of the vivado project by executing the project
    tcl file in batch mode.
    """
    def build_main(self):
        utils.Launcher('vivado', ['-mode', 'batch', '-source',
                                  self.name+'.tcl'],
                       cwd = self.work_root,
                       shell=platform.system() == 'Windows',
                       errormsg = "Failed to build FPGA bitstream").run()

    """ Program the FPGA

    For programming the FPGA a vivado tcl script is written that searches for the
    correct FPGA board and then downloads the bitstream. The tcl script is then
    executed in Vivado's batch mode.
    """
    def run(self, remaining):
        tcl_file_name = self.name+"_pgm.tcl"
        self._write_program_tcl_file(tcl_file_name)
        utils.Launcher('vivado', ['-mode', 'batch', '-source', tcl_file_name ],
                       cwd = self.work_root,
                       errormsg = "Failed to program the FPGA").run()

    """ Write the programming TCL file """
    def _write_program_tcl_file(self, program_tcl_filename):
        template_vars = {}
        template_vars['bitstream_name'] = self.name+'.bit'
        template_vars['hw_device'] = self.tool_options['hw_device']

        template = self.jinja_env.get_template('vivado/vivado-program.tcl.j2')  
        tcl_file_path = os.path.join(self.work_root, program_tcl_filename)    
        with open(tcl_file_path, 'w') as program_tcl_file:
            program_tcl_file.write(template.render(template_vars))
