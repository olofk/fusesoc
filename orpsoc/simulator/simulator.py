from orpsoc.config import Config
import shutil
import os
class Simulator(object):

    def __init__(self, system):
        config = Config()
        self.system = system
        self.build_root = os.path.join(config.build_root, self.system.name)
        self.cores_root = config.cores_root
        self.systems_root = config.systems_root

        self.src_root = os.path.join(self.build_root, 'src')

        self.include_dirs = []
        self.rtl_files = []
        self.tb_files = []
        for core_name in self.system.get_cores():
            core = self.system.cores[core_name]
            self.include_dirs += [os.path.join(self.src_root, core_name, d) for d in core.include_dirs]
            self.rtl_files    += [os.path.join(self.src_root, core_name, f) for f in core.rtl_files]
            self.tb_files     += [os.path.join(self.src_root, core_name, f) for f in core.tb_files]

    def configure(self):
        if os.path.exists(self.sim_root):
            shutil.rmtree(self.sim_root)
        os.makedirs(self.sim_root)

        self.system.setup_cores()

        for name, core in self.system.get_cores().items():
            print("Preparing " + name)
            dst_dir = os.path.join(Config().build_root, self.system.name, 'src', name)
            core.setup()
            core.export(dst_dir)
            core.patch(dst_dir)
