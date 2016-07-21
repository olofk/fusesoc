from .simulator import Simulator
from fusesoc.utils import Launcher, pr_warn

class Ghdl(Simulator):

    TOOL_NAME = 'GHDL'
    def __init__(self, system):

        self.analyze_options = []
        self.run_options     = []
        if system.ghdl is not None:
            self.analyze_options = system.ghdl.analyze_options
            self.run_options     = system.ghdl.run_options
        super(Ghdl, self).__init__(system)

    def configure(self, args):
        super(Ghdl, self).configure(args)

    def build(self):
        super(Ghdl, self).build()

        (src_files, incdirs) = self._get_fileset_files(['sim', 'ghdl'])

        cmd = 'ghdl'
        for f in src_files:
            args = ['-a']
            args += self.analyze_options[:]
            _supported = True
            if not f.logical_name:
                f.logical_name = 'work'
            if f.file_type == "vhdlSource":
                pass
            elif f.file_type == "vhdlSource-87":
                args += ['--std=87']
            elif f.file_type == "vhdlSource-93":
                args += ['--std=93']
            elif f.file_type == "vhdlSource-2008":
                args += ['--std=08']
            else:
                _s = "{} has unknown file type '{}'"
                pr_warn(_s.format(f.name,
                                  f.file_type))
                _supported = False
            if _supported:
                args += ['--work='+f.logical_name]
                args += [f.name]
                Launcher(cmd, args,
                         cwd      = self.sim_root,
                         errormsg = "Failed to analyze {}".format(f.name)).run()
        Launcher(cmd, ['-e', self.toplevel],
                 cwd = self.sim_root,
                 errormsg = "Failed to elaborate {}".format(self.toplevel)).run()

    def run(self, args):
        super(Ghdl, self).run(args)

        cmd = 'ghdl'
        args = ['-r']
        args += self.run_options
        args += [self.toplevel]
        Launcher(cmd, args,
                 cwd      = self.sim_root,
                 errormsg = "Simulation failed").run()

        super(Ghdl, self).done(args)
