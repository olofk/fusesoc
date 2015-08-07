import os
from fusesoc.simulator.simulator import Simulator
import logging
from fusesoc.utils import Launcher, pr_err

logger = logging.getLogger(__name__)

class Isim(Simulator):

    TOOL_NAME = 'ISIM'
    def __init__(self, system):

        self.cores = []
        self.isim_options = []

        if system.isim is not None:
            self.isim_options = system.isim.isim_options
        super(Isim, self).__init__(system)
        self.sim_root = os.path.join(self.build_root, 'sim-isim')




    def configure(self):
        super(Isim, self).configure()
        self._write_config_files()

    def _write_config_files(self):
        isim_file = 'isim.prj'
        f1 = open(os.path.join(self.sim_root,isim_file),'w')
        for src_file in self.verilog.src_files:
            f1.write('verilog work ' + os.path.relpath(src_file, self.sim_root) + '\n')
        for src_file in self.verilog.tb_src_files:
            f1.write('verilog work ' + os.path.relpath(src_file, self.sim_root) + '\n')
        f1.close()

        tcl_file = 'isim.tcl'
        f2 = open(os.path.join(self.sim_root,tcl_file),'w')
        f2.write('wave log -r /\n')
        f2.write('run all\n')
        f2.close()

    def build(self):
        super(Isim, self).build()

        #Check if any VPI modules are present and display warning
        if len(self.vpi_modules) > 0:
            modules = [m['name'] for m in self.vpi_modules]
            pr_err('VPI modules not supported by Isim: %s' % ', '.join(modules))

        #Build simulation model
        args = []
        args += [ self.toplevel]
        args += ['-prj', 'isim.prj']
        args += ['-o', 'fusesoc.elf']

        for include_dir in self.verilog.include_dirs:
            args += ['-i', os.path.relpath(include_dir, self.sim_root)]
        for include_dir in self.verilog.tb_include_dirs:
            args += ['-i', os.path.relpath(include_dir, self.sim_root)]

        args += self.isim_options

        Launcher('fuse', args,
                 cwd      = self.sim_root,
                 errormsg = "Failed to compile Isim simulation model").run()

    def run(self, args):
        super(Isim, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr.
        args = []
        #args += ['-gui']                                  # Interactive
        args += ['-tclbatch', 'isim.tcl']                  # Simulation commands
        args += ['-log', 'isim.log']                       # Log file
        args += ['-wdb', 'isim.wdb']                       # Simulation waveforms database
        args += ['+'+s for s in self.plusargs]             # Plusargs
        Launcher('./fusesoc.elf', args,
                 cwd = self.sim_root,
                 errormsg = "Failed to run Isim simulation").run()

        super(Isim, self).done(args)
