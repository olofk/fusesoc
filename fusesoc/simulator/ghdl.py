from .simulator import Simulator
from fusesoc.utils import Launcher, pr_warn

class Ghdl(Simulator):

    def configure(self, args):
        super(Ghdl, self).configure(args)

    def build(self):
        super(Ghdl, self).build()

        (src_files, incdirs) = self._get_fileset_files(['sim', 'ghdl'])

        cmd = 'ghdl'
        # ghdl does not support mixing incompatible versions
        # specifying 93c as std should allow 87 syntax
        # 2008 can't be combined so try to parse everthing with 08 std
        has87 = has93 = has08 = False
        for f in src_files:
            if f.file_type == "vhdlSource-87":
                has87 = True
            elif f.file_type == "vhdlSource-93":
                has93 = True
            elif f.file_type == "vhdlSource-2008":
                has08 = True
        stdarg = []
        if has08:
            if has87 or has93:
                pr_warn("ghdl can't mix vhdlSource-2008 with other standard version\n"+
                        "Trying with treating all as vhdlSource-2008"
                )
            stdarg = ['--std=08']
        elif has87 and has93:
            stdarg = ['--std=93c']
        elif has87:
            stdarg = ['--std=87']
        elif has93:
            stdarg = ['--std=93']

        _vhdltypes = ("vhdlSource", "vhdlSource-87", "vhdlSource-93", "vhdlSource-2008")
        for f in src_files:
            args = ['-a']+stdarg
            if self.system.ghdl is not None:
                args += self.system.ghdl.analyze_options[:]
            if f.file_type in _vhdltypes:
                if f.logical_name:
                    args += ['--work='+f.logical_name]
                args += [f.name]
                Launcher(cmd, args,
                         cwd      = self.work_root,
                         errormsg = "Failed to analyze {}".format(f.name)).run()
            else:
                _s = "{} has unknown file type '{}'"
                pr_warn(_s.format(f.name,
                                  f.file_type))
        Launcher(cmd, ['-e']+stdarg+[self.toplevel],
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
