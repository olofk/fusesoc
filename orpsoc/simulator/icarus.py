import os
import os.path
import shutil
import subprocess
from orpsoc.config import Config

class SimulatorIcarus:

    def __init__(self, system):
        config = Config()
        self.system = system
        self.build_root = os.path.join(config.build_root, self.system.name)
        self.cores_root = config.cores_root
        self.systems_root = config.systems_root

    def prepare(self):
        self.system.setup_cores()
        #FIXME: Make build_root directory
        self.copy_files()
        self.patch_files()
        self.write_config_files()
        self.compile()

    def copy_files(self):
        for core_name in self.system.get_cores():
            core = self.system.cores[core_name]

            src_dir = core.get_root()
            dst_dir = os.path.join(self.build_root, 'src', core_name)
            
            if os.path.exists(dst_dir):
                shutil.rmtree(dst_dir)

            #FIXME: Separate tb_files to an own directory tree (src/tb/core_name ?)
            src_files = core.get_rtl_files() + core.get_include_files() + core.get_tb_files()

            dirs = list(set(map(os.path.dirname,src_files)))
            for d in dirs:
                os.makedirs(os.path.join(dst_dir, d))

            for f in src_files:
                shutil.copyfile(os.path.join(src_dir, f), 
                                os.path.join(dst_dir, f))

    def patch_files(self):
        #FIXME: Check for patch availability
        #FIXME: Use native python patch instead
        for core_name in self.system.get_cores():
            core = self.system.cores[core_name]
            patch_root = os.path.join(self.cores_root, core_name, 'patches')
            if os.path.exists(patch_root):
                print(core_name + " has patches")
                for f in os.listdir(patch_root):
                    print("Applying " + f)
                    subprocess.call(['patch','-p0',
                                    '-d', os.path.join(self.build_root,'src',core_name),
                                    '-i', os.path.join(patch_root, f)])

    def write_config_files(self):
        icarus_file = 'icarus.scr'
        sim_root = os.path.join(self.build_root, 'sim-icarus')
        if os.path.exists(sim_root):
            shutil.rmtree(sim_root)
        os.makedirs(sim_root)

        src_root = os.path.join(self.build_root, 'src')

        f = open(os.path.join(sim_root,icarus_file),'w')

        for core_name in self.system.get_cores():
            core = self.system.cores[core_name]
            for d in core.get_include_dirs():
                f.write("+incdir+" + os.path.join(src_root, core_name, d) + '\n')
            for rtl_file in core.get_rtl_files():
                f.write(os.path.join(src_root, core_name, rtl_file)+'\n')
            for tb_file in core.get_tb_files():
                f.write(os.path.join(src_root, core_name, tb_file)+'\n')

        f.close()
    def compile(self):
        #FIXME: Handle failures. Save stdout/stderr. Build vmem file from elf file argument
        print(subprocess.check_output(['iverilog',
                                       '-s', 'orpsoc_tb',
                                       '-c', 'icarus.scr',
                                       '-o', 'orpsoc.elf'],
                                      cwd = os.path.join(self.build_root, 'sim-icarus')))
    def run(self, vmem_file):
        #FIXME: Handle failures. Save stdout/stderr. Build vmem file from elf file argument
        shutil.copyfile(vmem_file, os.path.join(self.build_root, 'sim-icarus', 'sram.vmem'))
        print(subprocess.check_output(['vvp',
                                       '-l', 'icarus.log',
                                       'orpsoc.elf'],
                                      cwd = os.path.join(self.build_root, 'sim-icarus')))

