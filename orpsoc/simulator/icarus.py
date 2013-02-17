import os
import subprocess
from .simulator import Simulator
import logging

logger = logging.getLogger(__name__)

class SimulatorIcarus(Simulator):

    def __init__(self, system):
        logger.debug('__init__() *Entered*')
        super(SimulatorIcarus, self).__init__(system)
        self.sim_root = os.path.join(self.build_root, 'sim-icarus')

        if system.config.has_option('icarus', 'iverilog_options'):
            self.iverilog_options = system.config.get('icarus','iverilog_options').split()
            logger.debug("self.iverilog_options=" + str(self.iverilog_options))
        else:
            self.iverilog_options = []
            logger.debug("No icarus iverilog_options"); # TODO: Remove this temporary line
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

        for include_dir in self.include_dirs:
            f.write("+incdir+" + include_dir + '\n')
        for src_file in self.src_files:
            f.write(src_file + '\n')

        f.close()
        logger.debug('_write_config_files() -Done-')

    def build(self):
        logger.debug('build() *Entered*')
        super(SimulatorIcarus, self).build()
        
        #Build VPI modules
        for vpi_module in self.vpi_modules:
            try:
                subprocess.check_call(['iverilog-vpi', '--name='+vpi_module['name']] +
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
                            '-s', 'orpsoc_tb',
                            '-c', 'icarus.scr',
                            '-o', 'orpsoc.elf'] +
                           self.iverilog_options,
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
        logger.debug('run() -Done-')

