import os
from fusesoc.simulator.simulator import Simulator
import logging
from fusesoc.utils import Launcher

logger = logging.getLogger(__name__)

class SimulatorIcarus(Simulator):

    TOOL_NAME = 'ICARUS'
    def __init__(self, system):

        self.cores = []
        self.iverilog_options = []

        if system.icarus is not None:
            self.iverilog_options = system.icarus.iverilog_options
        super(SimulatorIcarus, self).__init__(system)
        self.sim_root = os.path.join(self.build_root, 'sim-icarus')




    def configure(self):
        super(SimulatorIcarus, self).configure()
        self._write_config_files()

    def _write_config_files(self):
        icarus_file = 'icarus.scr'

        f = open(os.path.join(self.sim_root,icarus_file),'w')

        for include_dir in self.verilog.include_dirs:
            f.write("+incdir+" + os.path.abspath(include_dir) + '\n')
        for src_file in self.verilog.src_files:
            f.write(os.path.abspath(src_file) + '\n')
        for include_dir in self.verilog.tb_include_dirs:
            f.write("+incdir+" + os.path.abspath(include_dir) + '\n')
        for src_file in self.verilog.tb_src_files:
            f.write(os.path.abspath(src_file) + '\n')

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
        args += ['-s', self.toplevel]
        args += ['-c', 'icarus.scr']
        args += ['-o', 'fusesoc.elf']
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
        args += ['+'+s for s in self.plusargs]             # Plusargs
        Launcher('vvp', args,
                 cwd = self.sim_root,
                 errormsg = "Failed to run Icarus Simulation").run()

        super(SimulatorIcarus, self).done(args)
