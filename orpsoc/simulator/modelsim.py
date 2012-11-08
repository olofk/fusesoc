import os
import subprocess
from .simulator import Simulator

class Modelsim(Simulator):

    def __init__(self, system):
        super(Modelsim, self).__init__(system)
        self.sim_root = os.path.join(self.build_root, 'sim-modelsim')

    def configure(self):
        super(Modelsim, self).configure()
        self._write_config_files()

    def _write_config_files(self):
        self.cfg_file = self.system.name+'.scr'

        f = open(os.path.join(self.sim_root,self.cfg_file),'w')

        for include_dir in self.include_dirs:
            f.write("+incdir+" + include_dir + '\n')
        for rtl_file in self.rtl_files:
            f.write(rtl_file + '\n')
        for tb_file in self.tb_files:
            f.write(tb_file + '\n')

        f.close()

    def build(self):
        super(Modelsim, self).build()
        self.model_tech = os.getenv('MODEL_TECH')
        if not self.model_tech:
            print("Environment variable MODEL_TECH was not found. It should be set to <modelsim install path>/bin")
            exit(1)

        #FIXME: Handle failures. Save stdout/stderr. Build vmem file from elf file argument
        try:
            subprocess.check_call([self.model_tech+'/vlib', 'work'],
                                  cwd = self.sim_root)

        except OSError:
            print("Error: Command vlib not found. Make sure it is in $PATH")
            exit(1)
        except CalledProcessError:
            print("Error: Failed to create library work")
            exit(1)

        try:
            subprocess.check_call([self.model_tech+'/vlog', '-f', self.cfg_file, '-quiet'],
                            cwd = self.sim_root)
        except OSError:
            print("Error: Command vlog not found. Make sure it is in $PATH")
            exit(1)
        except subprocess.CalledProcessError:
            print("Error: Failed to compile simulation model")
            exit(1)

        for vpi_module in self.vpi_modules:
            objs = []
            for src_file in vpi_module['src_files']:
                try:
                    subprocess.check_call(['gcc', '-c', '-fPIC', '-g','-m32','-DMODELSIM_VPI'] +
                                          ['-I'+self.model_tech+'/../include'] +
                                          ['-I'+s for s in vpi_module['include_dirs']] +
                                          [src_file],
                                          cwd = self.sim_root,
                                          stdin=subprocess.PIPE)
                except OSError:
                    print("Error: Command gcc not found. Make sure it is in $PATH")
                    exit(1)
                except subprocess.CalledProcessError:
                    print("Error: Compilation of "+src_file + "failed")
                    exit(1)

            try:
                subprocess.check_call(['ld', '-shared','-E','-melf_i386','-o',vpi_module['name']] +
                                      ['gdb.o','jp_vpi.o','rsp-rtl_sim.o'],
                                      #[os.path.splitext(s)[0]+'.o' for s in vpi_module['src_files']],
                                      cwd = self.sim_root,
                                      stdin=subprocess.PIPE)
            except OSError:
                print("Error: Command ld not found. Make sure it is in $PATH")
                exit(1)
            except subprocess.CalledProcessError:
                print("Error: Linking of "+vpi_module['name'] + " failed")
                exit(1)

    def run(self, args):
        super(Modelsim, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr. Build vmem file from elf file argument
        try:
            subprocess.check_call([self.model_tech+'/vsim', '-c', '-do', 'run -all'] +
                                  ['-pli'] + [s['name'] for s in self.vpi_modules] +
                                  ['work.orpsoc_tb'] +
                                  ['+'+s for s in self.plusargs],
                                  cwd = self.sim_root,
                                  stdin=subprocess.PIPE)
        except OSError:
            print("Error: Command vsim not found. Make sure it is in $PATH")
            exit(1)
        except subprocess.CalledProcessError:
            print("Error: Simulation failed")
            exit(1)
