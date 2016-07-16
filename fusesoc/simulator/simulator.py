import argparse
import os
import logging

from fusesoc.edatool import EdaTool
from fusesoc.utils import run_scripts

logger = logging.getLogger(__name__)

class FileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, [os.path.abspath(values[0])])

class Simulator(EdaTool):

    def __init__(self, system):
        super(Simulator, self).__init__(system)

        self.sim_root = os.path.join(self.build_root, 'sim-'+self.TOOL_NAME.lower())

        self.env['CORE_ROOT'] = os.path.abspath(self.system.core_root)
        self.env['SIM_ROOT'] = os.path.abspath(self.sim_root)
        self.env['SIMULATOR'] = self.TOOL_NAME

        logger.debug( "depend -->  " +str (self.cores))
        if 'toplevel' in self.system.simulator:
            self.toplevel = self.system.simulator['toplevel']
        else:
            self.toplevel = 'orpsoc_tb'

        self._get_vpi_modules()

    def _get_vpi_modules(self):
        self.vpi_modules = []
        for core_name in self.cores:
            core = self.cm.get_core(core_name)

            if core.vpi:
                vpi_module = {}
                core_root = os.path.join(self.src_root, core.sanitized_name)
                vpi_module['root']          = os.path.relpath(core_root, self.sim_root)
                vpi_module['include_dirs']  = [os.path.join(vpi_module['root'], d) for d in core.vpi.include_dirs]
                vpi_module['src_files']     = [os.path.abspath(os.path.join(core_root, f.name)) for f in core.vpi.src_files]
                vpi_module['name']          = core.sanitized_name
                vpi_module['libs']          = [l for l in core.vpi.libs]
                self.vpi_modules += [vpi_module]

    def _get_fileset_files(self, usage):
        incdirs = set()
        src_files = []
        for core_name in self.cores:
            core = self.cm.get_core(core_name)
            basepath = os.path.relpath(os.path.join(self.src_root, core.sanitized_name), self.sim_root)
            for fs in core.file_sets:
                if (set(fs.usage) & set(usage)) and ((str(core_name) == str(self.system.name)) or not fs.private):
                    for file in fs.file:
                        if file.is_include_file:
                            incdirs.add(os.path.join(basepath, os.path.dirname(file.name)))
                        else:
                            file.name = os.path.join(basepath, file.name)
                            src_files.append(file)

        return (src_files, incdirs)

    def configure(self, args, skip_params = False):
        if not skip_params:
            self.parse_args(args, 'sim', ['plusarg', 'vlogparam'])
        self.work_root = self.sim_root
        super(Simulator, self).configure(args)

    def build(self):
        for core_name in self.cores:
            core = self.cm.get_core(core_name)
            if core.scripts:
                run_scripts(core.scripts.pre_build_scripts,
                            core.core_root,
                            self.sim_root,
                            self.env)
        return

    def run(self, args):
        if not hasattr(self, 'plusarg'):
            self.parse_args(args, 'sim', ['plusarg', 'vlogparam'])
        for core_name in self.cores:
            core = self.cm.get_core(core_name)
            if core.scripts:
                run_scripts(core.scripts.pre_run_scripts,
                            core.core_root,
                            self.sim_root,
                            self.env)

    def done(self, args):

        for core_name in self.cores:
            core = self.cm.get_core(core_name)
            if core.scripts:
                run_scripts(core.scripts.post_run_scripts,
                            core.core_root,
                            self.sim_root,
                            self.env)
