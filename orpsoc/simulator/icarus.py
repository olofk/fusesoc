import os
import subprocess
from .simulator import Simulator
import logging
from orpsoc.utils import Launcher

logger = logging.getLogger(__name__)

class SimulatorIcarus(Simulator):

    TOOL_NAME = 'ICARUS'
    def __init__(self, system):
        logger.debug('__init__() *Entered*')
        super(SimulatorIcarus, self).__init__(system)
        self.sim_root = os.path.join(self.build_root, 'sim-icarus')

        logger.debug('__init__() -Done-')

    def configure(self):
        logger.debug('configure() *Entered*')
        super(SimulatorIcarus, self).configure()
        self._write_config_files()
        logger.debug('configure()  -Done-')

    def _write_config_files(self):
        logger.debug('_write_config_files() *Entered*')
        icarus_file = 'icarus.scr'

        f = open(os.path.join(self.sim_root,icarus_file),'w')

        for include_dir in self.verilog.include_dirs:
            f.write("+incdir+" + os.path.abspath(include_dir) + '\n')
        for src_file in self.verilog.src_files:
            f.write(os.path.abspath(src_file) + '\n')
        for include_dir in self.verilog.tb_include_dirs:
            f.write("+incdir+" + os.path.abspath(include_dir) + '\n')
        for src_file in self.verilog.tb_src_files:
            f.write(os.path.abspath(src_file) + '\n')

        f.close()
        logger.debug('_write_config_files() -Done-')

    def build(self):
        logger.debug('build() *Entered*')
        super(SimulatorIcarus, self).build()
        
        #Build VPI modules
        for vpi_module in self.vpi_modules:
            try:
                subprocess.check_call(['iverilog-vpi', '--name='+vpi_module['name']] +
                                      [s for s in vpi_module['libs']] +
                                      ['-I' + s for s in vpi_module['include_dirs']] +
                                      vpi_module['src_files'],
                                      stderr = open(os.path.join(self.sim_root,vpi_module['name']+'.log'),'w'),
                                      cwd = os.path.join(self.sim_root))
            except OSError:
                print("Error: Command iverilog-vpi not found. Make sure it is in $PATH")
                exit(1)
            except subprocess.CalledProcessError:
                print("Error: Failed to compile VPI library " + vpi_module['name'])
                exit(1)
                                      
        #Build simulation model
        if subprocess.call(['iverilog',
                            '-s', self.toplevel,
                            '-c', 'icarus.scr',
                            '-o', 'orpsoc.elf'] +
                           self.system.iverilog_options,
                           cwd = self.sim_root):
            print("Error: Compiled failed")
            exit(1)
        logger.debug('build() -Done-')
        
    def run(self, args):
        logger.debug('run() *Entered*')
        super(SimulatorIcarus, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr. Build vmem file from elf file argument
        if subprocess.call(['vvp', '-n', '-M.',
                            '-l', 'icarus.log'] +
                           ['-m'+s['name'] for s in self.vpi_modules] +
                           ['orpsoc.elf'] +
                           ['+'+s for s in self.plusargs],
                           cwd = self.sim_root,
                           stdin=subprocess.PIPE):  # Pipe to support Ctrl-C
            print("Error: Failed to run simulation")

        super(SimulatorIcarus, self).done(args)
        logger.debug('run() -Done-')
