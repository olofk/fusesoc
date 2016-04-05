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




    def configure(self, args):
        super(Isim, self).configure(args)
        self._write_config_files()

    def _write_config_files(self):
        isim_file = 'isim.prj'
        f1 = open(os.path.join(self.sim_root,isim_file),'w')
        self.incdirs = set()
        src_files = []

        (src_files, self.incdirs) = self._get_fileset_files(['sim', 'isim'])
        for src_file in src_files:
            f1.write('verilog work ' + src_file.name + '\n')

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

        for include_dir in self.incdirs:
            args += ['-i', include_dir]

        for key, value in self.vlogparam.items():
            args += ['--generic_top', '{}={}'.format(key, value)]
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
        # Plusargs
        for key, value in self.plusarg.items():
            args += ['-testplusarg', '{}={}'.format(key, value)]
        #FIXME Top-level parameters

        Launcher('./fusesoc.elf', args,
                 cwd = self.sim_root,
                 errormsg = "Failed to run Isim simulation").run()

        super(Isim, self).done(args)
