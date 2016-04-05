import os
import subprocess
from .simulator import Simulator
from fusesoc.config import Config
from fusesoc.utils import Launcher, pr_warn

class Modelsim(Simulator):

    TOOL_NAME = 'MODELSIM'
    def __init__(self, system):

        self.vlog_options = []
        self.vsim_options = []

        if system.modelsim is not None:
            self.vlog_options = system.modelsim.vlog_options
            self.vsim_options = system.modelsim.vsim_options
        super(Modelsim, self).__init__(system)
        self.model_tech = os.getenv('MODEL_TECH')
        if not self.model_tech:
            raise RuntimeError("Environment variable MODEL_TECH was not found. It should be set to <modelsim install path>/bin")

    def configure(self, args):
        super(Modelsim, self).configure(args)

    def build(self):
        super(Modelsim, self).build()

        (src_files, incdirs) = self._get_fileset_files(['sim', 'modelsim'])
        logfile = os.path.join(self.sim_root, 'vlog.log')
        vlog_include_dirs = ['+incdir+'+d for d in incdirs]
        for f in src_files:
            if not f.logical_name:
                f.logical_name = 'work'
            if not os.path.exists(os.path.join(self.sim_root, f.logical_name)):
                Launcher(self.model_tech+'/vlib', [f.logical_name],
                         cwd      = self.sim_root,
                         errormsg = "Failed to create library '{}'".format(f.logical_name)).run()

            if f.file_type in ["verilogSource",
		               "verilogSource-95",
		               "verilogSource-2001",
		               "verilogSource-2005"]:
                cmd = 'vlog'
                args = self.vlog_options[:]
                args += vlog_include_dirs
            elif f.file_type in ["systemVerilogSource",
			         "systemVerilogSource-3.0",
			         "systemVerilogSource-3.1",
			         "systemVerilogSource-3.1a"]:
                cmd = 'vlog'
                args = self.vlog_options[:]
                args += ['-sv']
                args += vlog_include_dirs
            elif f.file_type == 'vhdlSource':
                cmd = 'vcom'
                args = []
            elif f.file_type == 'vhdlSource-87':
                cmd = 'vcom'
                args = ['-87']
            elif f.file_type == 'vhdlSource-93':
                cmd = 'vcom'
                args = ['-93']
            elif f.file_type == 'vhdlSource-2008':
                cmd = 'vcom'
                args = ['-2008']
            else:
                _s = "{} has unknown file type '{}'"
                pr_warn(_s.format(f.name,
                                  f.file_type))
            if not Config().verbose:
                args += ['-quiet']
            args += ['-work', f.logical_name]
            args += [f.name]
            Launcher(os.path.join(self.model_tech, cmd), args,
                 cwd      = self.sim_root,
                 errormsg = "Failed to compile simulation model. Compile log is available in " + logfile).run()

        for vpi_module in self.vpi_modules:
            objs = []
            for src_file in vpi_module['src_files']:
                args = []
                args += ['-c']
                args += ['-std=c99']
                args += ['-fPIC']
                args += ['-fno-stack-protector']
                args += ['-g']
                args += ['-m32']
                args += ['-DMODELSIM_VPI']
                args += ['-I'+self.model_tech+'/../include']
                args += ['-I'+s for s in vpi_module['include_dirs']]
                args += [src_file]
                Launcher('gcc', args,
                         cwd      = self.sim_root,
                         errormsg = "Compilation of "+src_file + "failed").run()

            object_files = [os.path.splitext(os.path.basename(s))[0]+'.o' for s in vpi_module['src_files']]

            args = []
            args += ['-shared']
            args += ['-E']
            args += ['-melf_i386']
            args += ['-o', vpi_module['name']]
            args += object_files
            args += [s for s in vpi_module['libs']]
            Launcher('ld', args,
                     cwd      = self.sim_root,
                     errormsg = "Linking of "+vpi_module['name'] + " failed").run()

    def run(self, args):
        super(Modelsim, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr
        vpi_options = []
        for vpi_module in self.vpi_modules:
            vpi_options += ['-pli', vpi_module['name']]

        args = []
        args += ['-quiet']
        args += ['-c']
        args += ['-do', 'run -all']
        args += self.vsim_options
        args += vpi_options
        args += [self.toplevel]

        # Plusargs
        for key, value in self.plusarg.items():
            args += ['+{}={}'.format(key, value)]
        #Top-level parameters
        for key, value in self.vlogparam.items():
            args += ['-g{}={}'.format(key, value)]

        Launcher(self.model_tech+'/vsim', args,
                 cwd      = self.sim_root,
                 errormsg = "Simulation failed. Simulation log is available in '{}'".format(os.path.join(self.sim_root, 'transcript'))).run()

        super(Modelsim, self).done(args)
