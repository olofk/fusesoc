import os
from fusesoc.simulator.simulator import Simulator
import logging
from fusesoc.utils import Launcher, pr_err, pr_warn

logger = logging.getLogger(__name__)

class Xsim(Simulator):

    TOOL_NAME = 'XSIM'
    def __init__(self, system):
        super(Xsim, self).__init__(system)

        self.top_module = None
        self.part = None

        if system.xsim is not None:
            self.top_module = system.xsim.top_module
            self.part = system.xsim.part

        if self.top_module == '':
            raise OptionSectionMissing('top_module')


    def configure(self, args):
        super(Xsim, self).configure(args)

        self.simcwd = os.path.join(self.work_root,
                                   self.system.sanitized_name+'.sim',
                                   'sim_1', 'behav')

        self._write_config_files()

    def _has_dpi(self):
        return (len(self.dpi_srcs) > 0)

    def _write_config_files(self):
        if self.top_module is None:
            pr_err("No top_module set for this simulation")
            exit(1)

        ip = []         # IP descriptions (xci files)
        constr = []     # Constraints (xdc files)
        verilog = []    # (System) Verilog files
        vhdl = []       # VHDL files

        (src_files, self.incdirs) = self._get_fileset_files(['sim', 'xsim'])

        for s in src_files:
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
            elif s.file_type in ("CPP", "C"):
                self.dpi_srcs.append(s.name)

        filename = self.system.sanitized_name+".tcl"
        path = os.path.join(self.work_root, filename)
        tcl_file = open(path, 'w')

        ipconfig = '\n'.join(['read_ip '+s for s in ip])+"\n"
        ipconfig += "upgrade_ip [get_ips]\n"
        ipconfig += "generate_target all [get_ips]\n"

        parameters = ""
        for key, value in self.vlogparam.items():
            parameters += "set_property generic {{{key}={value}}} [current_fileset -simset]".format(key=key, value=value)

        part = ""
        if self.part:
            part = " -part {} ".format(self.part)

        tcl_file.write(PROJECT_TCL_TEMPLATE.format(
            design       = self.system.sanitized_name,
            toplevel     = self.top_module,
            incdirs      = ' '.join(self.incdirs),
            parameters   = parameters,
            part         = part,
            ip           = ipconfig,
            src_files    = '\n'.join(['read_verilog '+s for s in verilog]+
                                     ['read_vhdl '+s for s in vhdl])))

        if self._has_dpi():
            tcl_file.write("set_property -name {xsim.elaborate.xelab.more_options} "
                           "-value {-cc gcc -sv_lib dpi } "
                           "-objects [current_fileset -simset]\n")

        tcl_file.write("launch_simulation -scripts_only")

        tcl_file.close()

        Launcher('vivado', ['-mode', 'batch', '-source',
                            os.path.join(self.work_root, self.system.sanitized_name+'.tcl')],
                 cwd = self.work_root,
                 errormsg = "Failed to build simulation").run()

    def build(self):
        super(Xsim, self).build()

        Launcher('./compile.sh',
                 cwd = self.simcwd,
                 errormsg = "Failed to build simulation").run()

        if self._has_dpi():
            args = ['-C', 'gcc', '-v' ]
            args += ['-additional_option', '-std=c++11' ]
            for l in self.dpi_libs:
                args += ['--additional_option']
                args += ['-l'+l]
            for src in self.dpi_srcs:
                args.append(os.path.join(self.work_root, src))

            Launcher('xsc', args, cwd = self.simcwd,
                     errormsg = "Failed to build DPI").run()

        Launcher('./elaborate.sh',
                 cwd = self.simcwd,
                 errormsg = "Failed to build simulation").run()

    def run(self, args):
        super(Xsim, self).run(args)

        simtcl = os.path.join(self.simcwd, self.top_module + ".tcl")
        print simtcl
        tcl_file = open(simtcl, "w")

        tcl_file.write("run -all")

        tcl_file.close()

        Launcher('./simulate.sh',
                 cwd = self.simcwd,
                 errormsg = "Failed to build simulation").run()

        super(Xsim, self).done(args)

""" Template for vivado project tcl file """
PROJECT_TCL_TEMPLATE = """# Auto-generated project tcl file

create_project {design} {part}

set_property "simulator_language" "Mixed" [current_project]

{ip}

{src_files}

{parameters}

set_property include_dirs [list {incdirs}] [current_fileset]
set_property top {toplevel} [current_fileset -simset]
"""
