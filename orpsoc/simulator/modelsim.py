import os
import subprocess
from .simulator import Simulator
from orpsoc.utils import Launcher

class Modelsim(Simulator):

    TOOL_NAME = 'MODELSIM'
    def __init__(self, system):
        super(Modelsim, self).__init__(system)
        self.model_tech = os.getenv('MODEL_TECH')
        if not self.model_tech:
            print("Environment variable MODEL_TECH was not found. It should be set to <modelsim install path>/bin")
            exit(1)
        self.sim_root = os.path.join(self.build_root, 'sim-modelsim')
        
    def configure(self):
        super(Modelsim, self).configure()
        self._write_config_files()

    def _write_config_files(self):
        self.cfg_file = self.system.name+'.scr'

        f = open(os.path.join(self.sim_root,self.cfg_file),'w')

        for include_dir in self.verilog.include_dirs:
            f.write("+incdir+" + include_dir + '\n')
        for src_file in self.verilog.src_files:
            f.write(src_file + '\n')
        for include_dir in self.verilog.tb_include_dirs:
            f.write("+incdir+" + include_dir + '\n')
        for src_file in self.verilog.tb_src_files:
            f.write(src_file + '\n')

        f.close()

    def build(self):
        super(Modelsim, self).build()

        #FIXME: Handle failures. Save stdout/stderr. Build vmem file from elf file argument
        try:
            Launcher(self.model_tech+'/vlib', ['work'], cwd = self.sim_root).run()
        except RuntimeError:
            print("Error: Failed to create library work")
            exit(1)
        try:
            logfile = os.path.join(self.sim_root, 'vlog.log')
            Launcher(self.model_tech+'/vlog', ['-f', self.cfg_file, '-quiet', '-l', logfile] +
                     self.system.vlog_options,
                     cwd = self.sim_root).run()
        except RuntimeError:
            print("Error: Failed to compile simulation model. Compile log is available in " + logfile)
            exit(1)

        for vpi_module in self.vpi_modules:
            objs = []
            for src_file in vpi_module['src_files']:
                try:
                    Launcher('gcc', ['-c', '-std=c99', '-fPIC', '-g','-m32','-DMODELSIM_VPI'] +
                             ['-I'+self.model_tech+'/../include'] +
                             ['-I'+s for s in vpi_module['include_dirs']] +
                             [src_file],
                             cwd = self.sim_root).run()
                except RuntimeError:
                    print("Error: Compilation of "+src_file + "failed")
                    exit(1)

                object_files = [os.path.splitext(os.path.basename(s))[0]+'.o' for s in vpi_module['src_files']]
            try:
                libs = [s for s in vpi_module['libs']]
                Launcher('ld', ['-shared','-E','-melf_i386','-o',vpi_module['name']] +
                         object_files + libs,
                         cwd = self.sim_root).run()
            except RuntimeError:
                print("Error: Linking of "+vpi_module['name'] + " failed")
                exit(1)

    def run(self, args):
        super(Modelsim, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr
        vpi_options = []
        for vpi_module in self.vpi_modules:
            vpi_options += ['-pli', vpi_module['name']]
        try:
            logfile = os.path.join(self.sim_root, 'vsim.log')
            Launcher(self.model_tech+'/vsim', ['-c', '-do', 'run -all'] +
                     ['-l', logfile] +
                     self.system.vsim_options +
                     vpi_options +
                     ['work.'+self.toplevel] +
                     ['+'+s for s in self.plusargs],
                     cwd = self.sim_root).run()
        except RuntimeError:
            print("Error: Simulation failed. Simulation log is available in " + logfile)
            exit(1)

        super(Modelsim, self).done(args)
