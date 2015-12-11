import os
import subprocess
from .simulator import Simulator
from fusesoc.utils import Launcher

class Modelsim(Simulator):

    TOOL_NAME = 'MODELSIM'
    def __init__(self, system):

        self.vlog_options = []
        self.vsim_options = []

        if system.modelsim is not None:
            self.vlog_options = system.modelsim.vlog_options
            self.vsim_options = system.modelsim.vsim_options
        super(Modelsim, self).__init__(system)
        self.model_tech = os.getenv('MODEL_TECH')
        if not self.model_tech:
            raise RuntimeError("Environment variable MODEL_TECH was not found. It should be set to <modelsim install path>/bin")
        self.sim_root = os.path.join(self.build_root, 'sim-modelsim')

    def configure(self):
        super(Modelsim, self).configure()
        self._write_config_files()

    def _write_config_files(self):
        self.cfg_file = self.system.name+'.scr'

        f = open(os.path.join(self.sim_root,self.cfg_file),'w')

        incdirs = set()
        src_files = []

        (src_files, incdirs) = self._get_fileset_files(['sim', 'modelsim'])

        for id in incdirs:
            f.write("+incdir+" + id + '\n')
        for src_file in src_files:
            f.write(src_file.name + '\n')

        f.close()

    def build(self):
        super(Modelsim, self).build()

        #FIXME: Handle failures. Save stdout/stderr.
        Launcher(self.model_tech+'/vlib', ['work'],
                 cwd      = self.sim_root,
                 errormsg = "Failed to create library 'work'").run()
        
        logfile = os.path.join(self.sim_root, 'vlog.log')
        args = []
        args += ['-f', self.cfg_file]
        args += ['-quiet']
        args += ['-l', logfile]
        args += self.vlog_options

        Launcher(self.model_tech+'/vlog', args,
                 cwd      = self.sim_root,
                 errormsg = "Failed to compile simulation model. Compile log is available in " + logfile).run()

        for vpi_module in self.vpi_modules:
            objs = []
            for src_file in vpi_module['src_files']:
                args = []
                args += ['-c']
                args += ['-std=c99']
                args += ['-fPIC']
                args += ['-fno-stack-protector']
                args += ['-g']
                args += ['-m32']
                args += ['-DMODELSIM_VPI']
                args += ['-I'+self.model_tech+'/../include']
                args += ['-I'+s for s in vpi_module['include_dirs']]
                args += [src_file]
                Launcher('gcc', args,
                         cwd      = self.sim_root,
                         errormsg = "Compilation of "+src_file + "failed").run()

            object_files = [os.path.splitext(os.path.basename(s))[0]+'.o' for s in vpi_module['src_files']]

            args = []
            args += ['-shared']
            args += ['-E']
            args += ['-melf_i386']
            args += ['-o', vpi_module['name']]
            args += object_files
            args += [s for s in vpi_module['libs']]
            Launcher('ld', args,
                     cwd      = self.sim_root,
                     errormsg = "Linking of "+vpi_module['name'] + " failed").run()

    def run(self, args):
        super(Modelsim, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr
        vpi_options = []
        for vpi_module in self.vpi_modules:
            vpi_options += ['-pli', vpi_module['name']]

        logfile = os.path.join(self.sim_root, 'vsim.log')
        args = []
        args += ['-quiet']
        args += ['-c']
        args += ['-do', 'run -all']
        args += ['-l', logfile]
        args += self.vsim_options
        args += vpi_options
        args += ['work.'+self.toplevel]
        args += ['+'+s for s in self.plusargs]

        Launcher(self.model_tech+'/vsim', args,
                 cwd      = self.sim_root,
                 errormsg = "Simulation failed. Simulation log is available in " + logfile).run()

        super(Modelsim, self).done(args)
