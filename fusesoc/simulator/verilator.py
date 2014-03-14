import os
import shutil
import subprocess

from fusesoc import utils
from fusesoc.core import OptionSectionMissing
from .simulator import Simulator

class Source(Exception):
     def __init__(self, value):
         self.value = value
     def __str__(self):
         return repr(self.value)


class Verilator(Simulator):

    TOOL_NAME = 'VERILATOR'
    def __init__(self, system):
        super(Verilator, self).__init__(system)

        self.verilator_options = []
        self.src_files = []
        self.include_files = []
        self.include_dirs = []
        self.tb_toplevel = ""
        self.src_type = ''
        self.define_files = []
        self.libs = []
        self.top_module = ""

        for core_name in self.cores:
            core = self.cm.get_core(core_name)
            self.src_files         += [os.path.join(self.src_root, core_name, f) for f in core.verilator.src_files]
            self.verilator_options += core.verilator.verilator_options
            self.include_files     += [os.path.join(self.src_root, core_name, f) for f in core.verilator.include_files]
            self.include_dirs      += [os.path.join(self.src_root, core_name, d) for d in core.verilator.include_dirs]
            self.define_files      += [os.path.join(self.src_root, core_name, f) for f in core.verilator.define_files]
            self.libs              += [l for l in core.verilator.libs]

        if system.verilator is not None:
             self.tb_toplevel        = system.verilator.tb_toplevel
             self.src_type           = system.verilator.source_type
             self.top_module         = system.verilator.top_module

        self.sim_root = os.path.join(self.build_root, 'sim-verilator')
        if self.top_module == '':
            raise OptionSectionMissing('top_module')
        if self.tb_toplevel == '':
            raise OptionSectionMissing('tb_toplevel')


    def export(self):
        src_file = os.path.join(self.system.core_root, self.tb_toplevel)
        dst_dir = os.path.join(self.sim_root, self.system.name)
        src_dir = os.path.dirname(self.tb_toplevel)

        if not os.path.exists(os.path.join(dst_dir, src_dir)):
            os.makedirs(os.path.join(dst_dir, src_dir))

        if(os.path.exists(src_file)):
            shutil.copyfile(os.path.join(src_file),
                            os.path.join(dst_dir, self.tb_toplevel))

    def configure(self):
        super(Verilator, self).configure()
        self.export()
        self._write_config_files()
        self.object_files = [os.path.splitext(os.path.basename(s))[0]+'.o' for s in self.src_files]

    def _write_config_files(self):
        self.verilator_file = 'input.vc'
        f = open(os.path.join(self.sim_root,self.verilator_file),'w')

        for include_dir in self.verilog.include_dirs:
            f.write("+incdir+" + os.path.abspath(include_dir) + '\n')
        for src_file in self.verilog.src_files:
            f.write(os.path.abspath(src_file) + '\n')
        f.close()
        #convert verilog defines into C file
        for files in self.define_files:
            read_file = os.path.join(self.src_root,files)
            write_file = os.path.join(os.path.dirname(os.path.join(self.sim_root,self.tb_toplevel)),os.path.splitext(os.path.basename(files))[0]+'.h')
            utils.convert_V2H(read_file, write_file)

    def _verilate(self):
        if self.src_type == 'systemC':
            args = ['--sc']
        else:
            args = ['--cc']
        args += ['-f', self.verilator_file]
        args += ['--top-module', self.top_module]
        args += ['--exe']
        args += ['-LDFLAGS "']
        args += [os.path.join(self.sim_root, s) for s in self.object_files]
        args += ['-Wl,--start-group']
        args += [l for l in self.libs]
        args += ['-Wl,--end-group']
        args += ['"']
        args += ['-CFLAGS ' + '-I' + i for i in self.include_dirs]
        args += [os.path.join(self.sim_root, self.system.name, self.tb_toplevel)]
        args += self.verilator_options

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
        super(Verilator, self).build()
        self._verilate()
        if self.src_type == 'C' or self.src_type == '':
            self.build_C()
        elif self.src_type == 'systemC':
            self.build_SysC()
        else:
            raise Source(self.src_type)

        utils.Launcher('make', ['-f', 'V' + self.top_module + '.mk', 'V' + self.top_module],
                       cwd=os.path.join(self.sim_root, 'obj_dir')).run()
     
    def build_C(self):
        args = ['-c']
        args += ['-std=c99']
        args += ['-I'+s for s in self.include_dirs]
        for src_file in self.src_files:
            src_file = os.path.join(self.sim_root, src_file)
            print("Compiling " + src_file)
            utils.Launcher('gcc',
                         args + [src_file],
                         cwd=self.sim_root).run()


    def build_SysC(self):
        #src_files        
        args = ['-I.']
        args += ['-MMD']
        args += ['-I'+s for s in self.include_dirs]
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

        for src_file in self.src_files:
            src_file = os.path.join(self.sim_root, src_file)
            print("Compiling " + src_file)
            utils.Launcher('g++',args + ['-o' + os.path.splitext(os.path.basename(src_file))[0]+'.o']+ [src_file],
                           cwd=self.sim_root).run()

    def run(self, args):
        #TODO: Handle arguments parsing
        utils.Launcher('./V' + self.top_module,
                       args,
                       cwd=os.path.join(self.sim_root, 'obj_dir')).run()
