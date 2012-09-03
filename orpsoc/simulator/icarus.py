import os
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

        for name, core in self.system.get_cores().items():
            print("Preparing " + name)
            dst_dir = os.path.join(Config().build_root, self.system.name, 'src', name)
            core.setup()
            core.export(dst_dir)
            core.patch(dst_dir)
        self.write_config_files()
        self.compile()

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
            for d in core.include_dirs:
                f.write("+incdir+" + os.path.join(src_root, core_name, d) + '\n')
            for rtl_file in core.rtl_files:
                f.write(os.path.join(src_root, core_name, rtl_file)+'\n')
            for tb_file in core.tb_files:
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

