import os
import shutil
import subprocess

from fusesoc import utils
from fusesoc.coremanager import CoreManager
from fusesoc.core import OptionSectionMissing
from .simulator import Simulator

class Source(Exception):
     def __init__(self, value):
         self.value = value
     def __str__(self):
         return repr(self.value)


class SimulatorVerilator(Simulator):

    TOOL_NAME = 'VERILATOR'
    def __init__(self, system):
        self.cores = []
        super(SimulatorVerilator, self).__init__(system)
        self.sim_root = os.path.join(self.build_root, 'sim-verilator')
        core = CoreManager().get_core(system.name)
        if core.verilator.top_module == '':
            raise OptionSectionMissing('top_module')
        if core.verilator.tb_toplevel == '':
            raise OptionSectionMissing('tb_toplevel')

    def configure(self):
        super(SimulatorVerilator, self).configure()
        self._write_config_files()
        self.object_files = [os.path.splitext(os.path.basename(s))[0]+'.o' for s in self.verilator.src_files]

    def _write_config_files(self):
        self.verilator_file = 'input.vc'
        f = open(os.path.join(self.sim_root,self.verilator_file),'w')

        for include_dir in self.verilog.include_dirs:
            f.write("+incdir+" + os.path.abspath(include_dir) + '\n')
        for src_file in self.verilog.src_files:
            f.write(os.path.abspath(src_file) + '\n')
        f.close()
        #convert verilog defines into C file
        for files in self.verilator.define_files:
            read_file = os.path.join(self.src_root,files)
            write_file = os.path.join(os.path.dirname(os.path.join(self.sim_root,self.verilator.tb_toplevel)),os.path.splitext(os.path.basename(files))[0]+'.h')
            utils.convert_V2H(read_file, write_file)

    def _verilate(self):
        if self.verilator.src_type == 'systemC':
            args = ['--sc']
        else:
            args = ['--cc']
        args += ['-f', self.verilator_file]
        args += ['--top-module', self.verilator.top_module]
        args += ['--exe']
        args += ['-LDFLAGS "']
        args += [os.path.join(self.sim_root, s) for s in self.object_files]
        args += ['--start-group']
        args += [l for l in self.verilator.libs]
        args += ['--end-group']
        args += ['"']
        args += ['-CFLAGS ' + '-I' + i for i in self.verilator.include_dirs]
        args += [self.verilator.tb_toplevel]
        args += self.verilator.verilator_options

        self.verilator_root = os.getenv('VERILATOR_ROOT')
        if self.verilator_root is None:
            try:
                output = subprocess.check_output(["which", "verilator"])
            except subprocess.CalledProcessError:
                 print("VERILATOR_ROOT not set and there is no verilator program in your PATH")
                 exit(1)
            print("VERILATOR_ROOT not set, fusesoc will use " + output)
            cmd = 'verilator'
        else:
            cmd = os.path.join(self.verilator_root,'bin','verilator')

        cmd += ' ' + ' '.join(args)
        l = utils.Launcher(cmd,
                           shell=True,
                           cwd = self.sim_root,
                           stderr = open(os.path.join(self.sim_root,'verilator.log'),'w')
        )
        print(l)
        l.run()

    def build(self):
        super(SimulatorVerilator, self).build()
        self._verilate()
        if self.verilator.src_type == 'C':
            self.build_C()
        elif self.verilator.src_type == 'systemC':
            self.build_SysC()
        else:
            raise Source(self.src_type)

        utils.Launcher('make', ['-f', 'V' + self.verilator.top_module + '.mk', 'V' + self.verilator.top_module],
                       cwd=os.path.join(self.sim_root, 'obj_dir')).run()
     
    def build_C(self):
        args = ['-c']
        args += ['-std=c99']
        args += ['-I'+s for s in self.verilator.include_dirs]
        for src_file in self.verilator.src_files:
            print("Compiling " + src_file)
            utils.Launcher('gcc',
                         args + [src_file],
                         cwd=self.sim_root).run()


    def build_SysC(self):
        #src_files        
        args = ['-I.']
        args += ['-MMD']
        args += ['-I'+s for s in self.verilator.include_dirs]
        args += ['-Iobj_dir']
        args += ['-I'+os.path.join(self.verilator_root,'include')]
        args += ['-I'+os.path.join(self.verilator_root,'include', 'vltstd')]  
        args += ['-DVL_PRINTF=printf']
        args += ['-DVM_TRACE=1']
        args += ['-DVM_COVERAGE=0']
        args += ['-I'+os.getenv('SYSTEMC_INCLUDE')]
        args += ['-Wno-deprecated']
        if os.getenv('SYSTEMC_CXX_FLAGS'):
             args += [os.getenv('SYSTEMC_CXX_FLAGS')]
        args += ['-c']
        args += ['-g']

        for src_file in self.verilator.src_files:
            print("Compiling " + src_file)
            utils.Launcher('g++',args + ['-o' + os.path.splitext(os.path.basename(src_file))[0]+'.o']+ [src_file],
                           cwd=self.sim_root).run()

    def run(self, args):
        #TODO: Handle arguments parsing
        utils.Launcher('./V' + self.verilator.top_module,
                       args,
                       cwd=os.path.join(self.sim_root, 'obj_dir')).run()
