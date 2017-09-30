import os
from .simulator import Simulator
import logging
from fusesoc.utils import Launcher

logger = logging.getLogger(__name__)

class Icarus(Simulator):

    MAKEFILE_TEMPLATE = """
all: $(VPI_MODULES) $(TARGET)

$(TARGET):
	iverilog -s$(TOPLEVEL) -c $(TARGET).scr -o $@ $(IVERILOG_OPTIONS)

clean:
	$(RM) $(VPI_MODULES) $(TARGET)
"""

    VPI_MAKE_SECTION = """
{name}_LIBS := {libs}
{name}_INCS := {incs}
{name}_SRCS := {srcs}

{name}.vpi: $({name}_SRCS)
	iverilog-vpi --name={name} $({name}_LIBS) $({name}_INCS) $?

clean_{name}:
	$(RM) {name}.vpi
"""

    def configure(self, args):
        super(Icarus, self).configure(args)
        self._write_config_files()

    def _write_config_files(self):
        f = open(os.path.join(self.work_root, self.name+'.scr'),'w')

        (src_files, incdirs) = self._get_fileset_files()
        for key, value in self.vlogdefine.items():
            f.write('+define+{}={}\n'.format(key, self._param_value_str(value, strings_in_quotes=True)))

        for key, value in self.vlogparam.items():
            f.write('+parameter+{}.{}={}\n'.format(self.toplevel, key, self._param_value_str(value, strings_in_quotes=True)))
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
            elif src_file.file_type == 'user':
                pass
            else:
                _s = "{} has unknown file type '{}'"
                logger.warning(_s.format(src_file.name, src_file.file_type))

        f.close()

        with open(os.path.join(self.work_root, 'Makefile'), 'w') as f:

            f.write("TARGET           := {}\n".format(self.name))
            _vpi_modules = ' '.join([m['name']+'.vpi' for m in self.vpi_modules])
            if _vpi_modules:
                f.write("VPI_MODULES      := {}\n".format(_vpi_modules))
            f.write("TOPLEVEL         := {}\n".format(self.toplevel))
            if 'iverilog_options' in self.tool_options:
                f.write("IVERILOG_OPTIONS := {}\n".format(' '.join(self.tool_options['iverilog_options'])))

            f.write(self.MAKEFILE_TEMPLATE)

            for vpi_module in self.vpi_modules:
                _incs = ['-I' + os.path.relpath(s, self.work_root) for s in vpi_module['include_dirs']]
                _libs = ['-l'+l for l in vpi_module['libs']]
                _srcs = [os.path.relpath(_f, self.work_root) for _f in vpi_module['src_files']]
                f.write(self.VPI_MAKE_SECTION.format(name = vpi_module['name'],
                                                     libs = ' '.join(_libs),
                                                     incs = ' '.join(_incs),
                                                     srcs = ' '.join(_srcs)))

    def run(self, args):
        super(Icarus, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr.
        args = []
        args += ['-n']                                     # Non-interactive ($stop = $finish)
        args += ['-M.']                                    # VPI module directory is '.'
        args += ['-l', 'icarus.log']                       # Log file
        args += ['-m'+s['name'] for s in self.vpi_modules] # Load VPI modules
        args += [self.name]                                # Simulation binary file
        args += ['-lxt2']

        # Plusargs
        for key, value in self.plusarg.items():
            args += ['+{}={}'.format(key, self._param_value_str(value))]

        Launcher('vvp', args,
                 cwd = self.work_root,
                 errormsg = "Failed to run Icarus Simulation").run()

        super(Icarus, self).done(args)
