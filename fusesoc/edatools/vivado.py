import os.path
import platform
from fusesoc import utils

from .backend import Backend

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
class Vivado(Backend):

    argtypes = ['vlogdefine', 'vlogparam']

    """ Configuration is the first phase of the build

    In the vivado backend the project TCL is written and all files are copied
    """
    def configure(self, args):
        super(Vivado, self).configure(args)

        if not 'part' in self.tool_options:
            raise RuntimeError("Missing required option '{}'".format('part'))
        self._write_project_tcl_file()

    """ Write the project tcl file

    This writes the project tcl file. It first collects all sources, ip and contraints
    and then writes them to the tcl file along with the build steps.
    """
    def _write_project_tcl_file(self):
        # Get the synthesis files and files specific to vivado
        (src, incdirs) = self._get_fileset_files(force_slash=True)

        ip = []             # IP descriptions (xci files)
        constr = []         # Constraints (xdc files)
        verilog = []        # Verilog files
        sverilog = []       # System Verilog files
        vhdl = []           # VHDL files
        hasVhdl2008 = False # Has VHDL 2008 files
        tcl = []            # TCL files to include

        ipconfig = ""

        for s in src:
            if s.file_type == 'xci':
                ip.append(s.name)
            elif s.file_type == 'xdc':
                constr.append(s.name)
            elif s.file_type.startswith('verilogSource'):
                verilog.append(s.name)
            elif s.file_type.startswith('systemVerilogSource'):
                sverilog.append(s.name)
            elif s.file_type.startswith('vhdlSource'):
                params = ""
                if s.file_type == "vhdlSource-2008":
                    params += "-vhdl2008 "
                    hasVhdl2008 = True
                if s.logical_name:
                    params += "-library {} ".format(s.logical_name)
                vhdl.append(params+s.name)
            elif s.file_type.startswith('tclSource'):
                tcl.append(s.name)
            elif s.file_type == 'user':
                pass

        tcl_file = open(os.path.join(self.work_root, self.name+".tcl"), 'w')

        if len(ip)>0:
            ipconfig += '\n'.join(['read_ip '+s for s in ip])+"\n"
            ipconfig += "upgrade_ip [get_ips]\n"
            ipconfig += "generate_target all [get_ips]\n"

        extras = ''
        if hasVhdl2008:
            extras += "set_param project.enableVHDL2008 1\n"

        parameters = ""

        if len(self.vlogparam.items()) > 0:
            generics = " ".join(k+"="+self._param_value_str(v) for k,v in self.vlogparam.items())
            parameters += "set_property generic {"+generics+"} [get_filesets sources_1]\n"

        if len(self.vlogdefine.items()) > 0:
            defines = " ".join(k+"="+self._param_value_str(v) for k,v in self.vlogdefine.items())
            parameters += "set_property verilog_define \""+defines+"\" [get_filesets sources_1]\n"

        if self.toplevel:
            extras += "set_property top "+self.toplevel+" [current_fileset]"

        # Write the formatted string to the tcl file
        tcl_file.write(PROJECT_TCL_TEMPLATE.format(
            design       = self.name,
            part         = self.tool_options['part'],
            bitstream    = self.name+'.bit',
            incdirs      = ' '.join(incdirs),
            ip           = ipconfig,
            parameters   = parameters,
            extras       = extras,
            tcl          = '\n'.join(['source '+s for s in tcl]),
            src_files    = '\n'.join(['read_verilog '+s for s in verilog]+
                                     ['read_verilog -sv '+s for s in sverilog]+
                                     ['read_vhdl '+s for s in vhdl]),
            xdc_files    = '\n'.join(['read_xdc '+s for s in constr])))

        tcl_file.close()

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
        tcl_file_name = os.path.join(self.work_root, self.name+"_pgm.tcl")
        self._write_program_tcl_file(tcl_file_name)
        utils.Launcher('vivado', ['-mode', 'batch', '-source', tcl_file_name ],
                       cwd = self.work_root,
                       errormsg = "Failed to program the FPGA").run()

    """ Write the programming TCL file """
    def _write_program_tcl_file(self, program_tcl_filename):
        tcl_file = open(program_tcl_filename, 'w')
        tcl_file.write(PROGRAM_TCL_TEMPLATE.format(
            bitstream    = self.name+'.bit',
            hw_device = self.tool_options['hw_device']
        ))
        tcl_file.close()


""" Template for vivado project tcl file """
PROJECT_TCL_TEMPLATE = """# Auto-generated project tcl file

create_project -part "{part}" {design}

set_property "simulator_language" "Mixed" [current_project]

{tcl}

{ip}

{src_files}

{parameters}

set_property include_dirs [list {incdirs}] [get_filesets sources_1]

{xdc_files}

{extras}

# By default create_project creates the synth_1 and impl_1 runs.
# To explicitly create customized runs, uncomment the code below.
#regexp -- {{Vivado v([0-9]{{4}})\.[0-9]}} [version] -> year
#create_run synth_1 -quiet -flow "Vivado Synthesis $year" -strategy "Vivado Synthesis Defaults"
#create_run impl_1 -quiet -flow "Vivado Implementation $year" -strategy "Vivado Implementation Defaults" -parent_run synth_1
#current_run [get_runs synth_1]

launch_runs impl_1
wait_on_run impl_1
open_run impl_1
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
