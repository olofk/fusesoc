import os
from fusesoc.simulator.simulator import Simulator
import logging
from fusesoc.utils import Launcher, pr_warn

logger = logging.getLogger(__name__)

class Icarus(Simulator):

    def configure(self, args):
        super(Icarus, self).configure(args)
        self._write_config_files()

    def _write_config_files(self):
        icarus_file = 'icarus.scr'

        f = open(os.path.join(self.work_root,icarus_file),'w')

        incdirs = set()
        src_files = []

        (src_files, incdirs) = self._get_fileset_files(['sim', 'icarus'])
        for id in incdirs:
            f.write("+incdir+" + id+'\n')
        for src_file in src_files:
            if src_file.file_type in ["verilogSource",
		                      "verilogSource-95",
		                      "verilogSource-2001",
		                      "verilogSource-2005",
                                      "systemVerilogSource",
			              "systemVerilogSource-3.0",
			              "systemVerilogSource-3.1",
			              "systemVerilogSource-3.1a"]:
                f.write(src_file.name+'\n')
            else:
                _s = "{} has unknown file type '{}'"
                pr_warn(_s.format(src_file.name,
                                  src_file.file_type))

        f.close()

    def build(self):
        super(Icarus, self).build()
        
        #Build VPI modules
        for vpi_module in self.vpi_modules:
            args = []
            args += ['--name='+vpi_module['name']]
            args += [s for s in vpi_module['libs']]
            args += ['-I' + s for s in vpi_module['include_dirs']]
            args += vpi_module['src_files']

            Launcher('iverilog-vpi', args,
                     stderr   = open(os.path.join(self.work_root,vpi_module['name']+'.log'),'w'),
                     cwd      = os.path.join(self.work_root),
                     errormsg = "Failed to compile VPI library " + vpi_module['name']).run()
                                      
        #Build simulation model
        args = []
        args += ['-s'+s for s in self.toplevel.split(' ')]
        args += ['-c', 'icarus.scr']
        args += ['-o', 'fusesoc.elf']

        for key, value in self.vlogdefine.items():
            args += ['-D{}={}'.format(key, value)]

        for key, value in self.vlogparam.items():
            #Workaround since Icarus treats all unqouted strings containing 'e' as floats
            if value == "true":
                value = "\"true\""
            print("'{}' '{}'".format(key, value))
            args += ['-P{}.{}={}'.format(self.toplevel, key, value)]
        if self.system.icarus is not None:
            args += self.system.icarus.iverilog_options

        Launcher('iverilog', args,
                 cwd      = self.work_root,
                 errormsg = "Failed to compile Icarus Simulation model").run()
        
    def run(self, args):
        super(Icarus, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr.
        args = []
        args += ['-n']                                     # Non-interactive ($stop = $finish)
        args += ['-M.']                                    # VPI module directory is '.'
        args += ['-l', 'icarus.log']                       # Log file
        args += ['-m'+s['name'] for s in self.vpi_modules] # Load VPI modules
        args += ['fusesoc.elf']                            # Simulation binary file
        args += ['-lxt2']

        # Plusargs
        for key, value in self.plusarg.items():
            args += ['+{}={}'.format(key, value)]
        #FIXME Top-level parameters
        Launcher('vvp', args,
                 cwd = self.work_root,
                 errormsg = "Failed to run Icarus Simulation").run()

        super(Icarus, self).done(args)
