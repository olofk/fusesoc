import os.path
import shutil
import subprocess
from fusesoc import utils

from fusesoc.build.backend import Backend

""" Vivado Backend

The Vivado backend executes Xilinx Vivado to build systems and program the FPGA.

The backend defines the following section:

    [vivado]
    part = <part name> # Format <family><device><package>-<speedgrade>
    hw_device = <device name> # Format <family><device>_0

A core (usually the system core) can add the following files:

- Standard design sources

- Constraints: Supply xdc files with file_type=xdc

- IP: Supply the IP core xdi file with file_type=xdi and other files (like .prj)
      as file_type=data
"""
class Vivado(Backend):
    """ Define the toolname. It is used by FuseSoC to select the backend"""
    TOOL_NAME = 'vivado'

    """ The constructor of the backend"""
    def __init__(self, system):
        # Do the general backend initialization
        super(Vivado, self).__init__(system)
        # Set work root. That is the name of the output path for build files
        self.work_root = os.path.join(self.build_root, 'bld-{}'.format(self.TOOL_NAME))

    """ Configuration is the first phase of the build

    In the vivado backend the project TCL is written and all files are copied
    """
    def configure(self, args):
        super(Vivado, self).configure(args)
        self._write_project_tcl_file()

    """ Write the project tcl file

    This writes the project tcl file. It first collects all sources, ip and contraints
    and then writes them to the tcl file along with the build steps.
    """
    def _write_project_tcl_file(self):
        ip = []      # IP descriptions (xci files)
        constr = []  # Constraints (xdc files)
        verilog = [] # (System) Verilog files
        vhdl = []    # VHDL files

        # Get the synthesis files and files specific to vivado
        (src, incdirs) = self._get_fileset_files(['vivado', 'synth'])
        for s in src:
            if s.file_type == 'xci':
                ip.append(s.name)
            elif s.file_type == 'xdc':
                constr.append(s.name)
            elif s.file_type.startswith('verilogSource'):
                verilog.append(s.name)
            elif s.file_type.startswith('systemVerilogSource'):
                verilog.append(s.name)
            elif s.file_type.startswith('vhdlSource'):
                vhdl.append(s.name)

        # Write the formatted string to the tcl file
        tcl_file = open(os.path.join(self.work_root, self.system.name+".tcl"), 'w')
        tcl_file.write(PROJECT_TCL_TEMPLATE.format(
            design       = self.system.name,
            part         = self.system.backend.part,
            bitstream    = os.path.join(self.work_root, self.system.name+'.bit'),
            incdirs      = ' '.join(incdirs),
            ip_files     = '\n'.join(['read_ip '+s for s in ip]),
            src_files    = '\n'.join(['read_verilog '+s for s in verilog]+
                                     ['read_vhdl '+s for s in vhdl]),
            xdc_files    = '\n'.join(['read_xdc '+s for s in constr])))
        tcl_file.close()

    """ Execute the build

    This launches the actual build of the vivado project by executing the project
    tcl file in batch mode.
    """
    def build(self, args):
        super(Vivado, self).build(args)

        utils.Launcher('vivado', ['-mode', 'batch', '-source',
                                  os.path.join(self.work_root, self.system.name+'.tcl')],
                       cwd = self.work_root,
                       errormsg = "Failed to build FPGA bitstream").run()
        
        super(Vivado, self).done()

    """ Program the FPGA

    For programming the FPGA a vivado tcl script is written that searches for the
    correct FPGA board and then downloads the bitstream. The tcl script is then
    executed in Vivado's batch mode.
    """
    def pgm(self, remaining):
        tcl_file_name = os.path.join(self.work_root, self.system.name+"_pgm.tcl")
        self._write_program_tcl_file(tcl_file_name)
        utils.Launcher('vivado', ['-mode', 'batch', '-source', tcl_file_name ],
                       cwd = self.work_root,
                       errormsg = "Failed to program the FPGA").run()

    """ Write the programming TCL file """
    def _write_program_tcl_file(self, program_tcl_filename):
        tcl_file = open(program_tcl_filename, 'w')
        tcl_file.write(PROGRAM_TCL_TEMPLATE.format(
            bitstream    = os.path.join(self.work_root, self.system.name+'.bit'),
            hw_device = self.system.backend.hw_device
        ))
        tcl_file.close()

""" Template for vivado project tcl file """
PROJECT_TCL_TEMPLATE = """# Auto-generated project tcl file

create_project -part {part} {design}

{ip_files}

{src_files}

set_property include_dirs [list {incdirs}] [current_fileset]

{xdc_files}

create_run -name synthesis -flow "Vivado Synthesis 2015" -strategy "Vivado Synthesis Defaults"
create_run implementation -flow "Vivado Implementation 2015" -strategy "Vivado Implementation Defaults" -parent_run synthesis

launch_runs implementation
wait_on_run implementation
open_run implementation
write_bitstream {bitstream}
"""

""" Template for vivado programming tcl file """
PROGRAM_TCL_TEMPLATE = """# Auto-generated program tcl file

open_hw
connect_hw_server

set board ""

foreach {{ target }} [get_hw_targets] {{
    puts "$target"
    current_hw_target $target
    open_hw_target
    if {{ [get_hw_devices] == "{hw_device}" }} {{
        set board [current_hw_target]
        break
    }}
    close_hw_target
}}

if {{ $board == "" }} {{
    puts "Did not find board"
    exit 1
}}

current_hw_device {hw_device}
set_property PROGRAM.FILE "{bitstream}" [current_hw_device]
program_hw_devices [current_hw_device]
"""
