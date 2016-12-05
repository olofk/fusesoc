from .simulator import Simulator
from fusesoc.utils import Launcher, pr_warn

class Ghdl(Simulator):

    def configure(self, args):
        super(Ghdl, self).configure(args)

    def build(self):
        super(Ghdl, self).build()

        (src_files, incdirs) = self._get_fileset_files(['sim', 'ghdl'])

        cmd = 'ghdl'
        for f in src_files:
            args = ['-a']
            if self.system.ghdl is not None:
                args += self.system.ghdl.analyze_options[:]
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
                         cwd      = self.work_root,
                         errormsg = "Failed to analyze {}".format(f.name)).run()
        Launcher(cmd, ['-e', self.toplevel],
                 cwd = self.work_root,
                 errormsg = "Failed to elaborate {}".format(self.toplevel)).run()

    def run(self, args):
        super(Ghdl, self).run(args)

        cmd = 'ghdl'
        args = ['-r']
        if self.system.ghdl is not None:
            args += self.system.ghdl.run_options
        args += [self.toplevel]
        Launcher(cmd, args,
                 cwd      = self.work_root,
                 errormsg = "Simulation failed").run()

        super(Ghdl, self).done(args)
