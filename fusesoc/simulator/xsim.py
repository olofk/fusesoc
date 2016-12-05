import os
from fusesoc.simulator.simulator import Simulator
import logging
from fusesoc.utils import Launcher, pr_err, pr_warn

logger = logging.getLogger(__name__)

class Xsim(Simulator):

    def configure(self, args):
        super(Xsim, self).configure(args)
        self._write_config_files()

    def _write_config_files(self):
        xsim_file = 'xsim.prj'
        f1 = open(os.path.join(self.work_root,xsim_file),'w')
        self.incdirs = set()
        src_files = []

        (src_files, self.incdirs) = self._get_fileset_files(['sim', 'xsim'])
        for src_file in src_files:
            if src_file.file_type in ["verilogSource",
		                      "verilogSource-95",
		                      "verilogSource-2001"]:
                f1.write('verilog work ' + src_file.name + '\n')
            elif src_file.file_type in ["vhdlSource",
                                        "vhdlSource-87",
                                        "vhdlSource-93"]:
                f1.write('vhdl work ' + src_file.logical_name + " " + src_file.name + '\n')
            elif src_file.file_type in ['vhdlSource-2008']:
                f1.write('vhdl2008 ' + src_file.logical_name + " " + src_file.name + '\n')
            elif src_file.file_type in ["systemVerilogSource",
                                        "systemVerilogSource-3.0",
                                        "systemVerilogSource-3.1",
                                        "systemVerilogSource-3.1a",
                                        "verilogSource-2005"]:
                f1.write('sv work ' + src_file.name + '\n')
            else:
                _s = "{} has unknown file type '{}'"
                pr_warn(_s.format(src_file.name,
                                  src_file.file_type))
        f1.close()

        tcl_file = 'xsim.tcl'
        f2 = open(os.path.join(self.work_root,tcl_file),'w')
        f2.write('add_wave -radix hex /\n')
        f2.write('run all\n')
        f2.close()

    def build(self):
        super(Xsim, self).build()

        #Check if any VPI modules are present and display warning
        if len(self.vpi_modules) > 0:
            modules = [m['name'] for m in self.vpi_modules]
            pr_err('VPI modules not supported by Xsim: %s' % ', '.join(modules))

        #Build simulation model
        args = []
        args += [ self.toplevel]
        args += ['--prj', 'xsim.prj']      # list of design files
        args += ['--timescale', '1ps/1ps'] # default timescale to prevent error if unspecified
        args += ['--snapshot', 'fusesoc']  # name of the design to simulate
        args += ['--debug', 'typical']     # capture waveforms

        for include_dir in self.incdirs:
            args += ['-i', include_dir]

        for key, value in self.vlogparam.items():
            args += ['--generic_top', '{}={}'.format(key, value)]

        if self.system.xsim is not None:
            args += self.system.xsim.xsim_options

        Launcher('xelab', args,
                 cwd      = self.work_root,
                 errormsg = "Failed to compile Xsim simulation model").run()

    def run(self, args):
        super(Xsim, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr.
        args = []
        args += ['--gui']                                 # Interactive
        args += ['--tclbatch', 'xsim.tcl']                 # Simulation commands
        args += ['--log', 'xsim.log']                      # Log file
        args += ['--wdb', 'xsim.wdb']                      # Simulation waveforms database
        args += ['fusesoc']                                # Snapshot name
        # Plusargs
        for key, value in self.plusarg.items():
            args += ['--testplusarg', '{}={}'.format(key, value)]
        #FIXME Top-level parameters

        Launcher('xsim', args,
                 cwd = self.work_root,
                 errormsg = "Failed to run Xsim simulation").run()

        super(Xsim, self).done(args)
