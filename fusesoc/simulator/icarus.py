import os
from fusesoc.simulator.simulator import Simulator
import logging
from fusesoc.utils import Launcher, pr_warn

logger = logging.getLogger(__name__)

class SimulatorIcarus(Simulator):

    TOOL_NAME = 'ICARUS'
    def __init__(self, system):

        self.cores = []
        self.iverilog_options = []

        if system.icarus is not None:
            self.iverilog_options = system.icarus.iverilog_options
        super(SimulatorIcarus, self).__init__(system)

    def configure(self, args):
        super(SimulatorIcarus, self).configure(args)
        self._write_config_files()

    def _write_config_files(self):
        icarus_file = 'icarus.scr'

        f = open(os.path.join(self.sim_root,icarus_file),'w')

        incdirs = set()
        src_files = []

        (src_files, incdirs) = self._get_fileset_files(['sim', 'icarus'])
        for id in incdirs:
            f.write("+incdir+" + id+'\n')
        for src_file in src_files:
            if src_file.file_type in ["verilogSource",
		                      "verilogSource-95",
		                      "verilogSource-2001",
		                      "verilogSource-2005",
                                      "systemVerilogSource",
			              "systemVerilogSource-3.0",
			              "systemVerilogSource-3.1",
			              "systemVerilogSource-3.1a"]:
                f.write(src_file.name+'\n')
            else:
                _s = "{} has unknown file type '{}'"
                pr_warn(_s.format(src_file.name,
                                  src_file.file_type))

        f.close()

    def build(self):
        super(SimulatorIcarus, self).build()
        
        #Build VPI modules
        for vpi_module in self.vpi_modules:
            args = []
            args += ['--name='+vpi_module['name']]
            args += [s for s in vpi_module['libs']]
            args += ['-I' + s for s in vpi_module['include_dirs']]
            args += vpi_module['src_files']

            Launcher('iverilog-vpi', args,
                     stderr   = open(os.path.join(self.sim_root,vpi_module['name']+'.log'),'w'),
                     cwd      = os.path.join(self.sim_root),
                     errormsg = "Failed to compile VPI library " + vpi_module['name']).run()
                                      
        #Build simulation model
        args = []
        args += ['-s'+s for s in self.toplevel.split(' ')]
        args += ['-c', 'icarus.scr']
        args += ['-o', 'fusesoc.elf']
        for key, value in self.vlogparam.items():
            args += ['-P{}.{}={}'.format(self.toplevel, key, value)]
        args += self.iverilog_options

        Launcher('iverilog', args,
                 cwd      = self.sim_root,
                 errormsg = "Failed to compile Icarus Simulation model").run()
        
    def run(self, args):
        super(SimulatorIcarus, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr.
        args = []
        args += ['-n']                                     # Non-interactive ($stop = $finish)
        args += ['-M.']                                    # VPI module directory is '.'
        args += ['-l', 'icarus.log']                       # Log file
        args += ['-m'+s['name'] for s in self.vpi_modules] # Load VPI modules
        args += ['fusesoc.elf']                            # Simulation binary file
        args += ['-lxt2']

        # Plusargs
        for key, value in self.plusarg.items():
            args += ['+{}={}'.format(key, value)]
        #FIXME Top-level parameters
        Launcher('vvp', args,
                 cwd = self.sim_root,
                 errormsg = "Failed to run Icarus Simulation").run()

        super(SimulatorIcarus, self).done(args)
