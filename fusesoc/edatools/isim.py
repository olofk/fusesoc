import os
from .simulator import Simulator
import logging
from fusesoc.utils import Launcher

logger = logging.getLogger(__name__)

class Isim(Simulator):

    def configure(self, args):
        super(Isim, self).configure(args)
        self._write_config_files()

    def _write_config_files(self):
        isim_file = 'isim.prj'
        f1 = open(os.path.join(self.work_root,isim_file),'w')
        self.incdirs = set()
        src_files = []

        (src_files, self.incdirs) = self._get_fileset_files()
        for src_file in src_files:
            if src_file.file_type in ["verilogSource",
                              "verilogSource-95",
                              "verilogSource-2001"]:
                f1.write('verilog work ' + src_file.name + '\n')
            elif src_file.file_type.startswith("vhdlSource"):
                f1.write('vhdl work ' + src_file.logical_name + " " + src_file.name + '\n')
            elif src_file.file_type in ["systemVerilogSource",
                                        "systemVerilogSource-3.0",
                                        "systemVerilogSource-3.1",
                                        "systemVerilogSource-3.1a",
                                        "verilogSource-2005"]:
                f1.write('sv work ' + src_file.name + '\n')
            elif src_file.file_type in ["user"]:
                pass
            else:
                _s = "{} has unknown file type '{}'"
                logger.warning(_s.format(src_file.name,
                               src_file.file_type))
        f1.close()

        tcl_file = 'isim.tcl'
        f2 = open(os.path.join(self.work_root,tcl_file),'w')
        f2.write('wave log -r /\n')
        f2.write('run all\n')
        f2.write('quit\n')
        f2.close()

    def build_main(self):
        #Check if any VPI modules are present and display warning
        if len(self.vpi_modules) > 0:
            modules = [m['name'] for m in self.vpi_modules]
            logger.error('VPI modules not supported by Isim: %s' % ', '.join(modules))

        #Build simulation model
        args = []
        args += self.toplevel.split()
        args += ['-prj', 'isim.prj']
        args += ['-o', 'fusesoc.elf']

        for include_dir in self.incdirs:
            args += ['-i', include_dir]

        for key, value in self.vlogparam.items():
            args += ['--generic_top', '{}={}'.format(key, self._param_value_str(value))]
        if 'isim_options' in self.tool_options:
            args += self.tool_options['isim_options']

        Launcher('fuse', args,
                 cwd      = self.work_root,
                 errormsg = "Failed to compile Isim simulation model").run()

    def run(self, args):
        super(Isim, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr.
        args = []
        #args += ['-gui']                                  # Interactive
        args += ['-tclbatch', 'isim.tcl']                  # Simulation commands
        args += ['-log', 'isim.log']                       # Log file
        args += ['-wdb', 'isim.wdb']                       # Simulation waveforms database
        # Plusargs
        for key, value in self.plusarg.items():
            args += ['-testplusarg', '{}={}'.format(key, value)]
        #FIXME Top-level parameters

        Launcher('./fusesoc.elf', args,
                 cwd = self.work_root,
                 errormsg = "Failed to run Isim simulation").run()

        super(Isim, self).done(args)
