import os
import logging

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Icarus(Edatool):

    tool_options = {
        'members' : {'timescale' : 'String'},
        'lists' : {'iverilog_options' : 'String'}
    }

    argtypes = ['plusarg', 'vlogdefine', 'vlogparam']

    MAKEFILE_TEMPLATE = """
all: $(VPI_MODULES) $(TARGET)

$(TARGET):
	iverilog -s$(TOPLEVEL) -c $(TARGET).scr -o $@ $(IVERILOG_OPTIONS)

run: $(VPI_MODULES) $(TARGET)
	vvp -n -M. -l icarus.log -lxt2 $(patsubst %.vpi,-m%,$(VPI_MODULES)) $(TARGET) $(EXTRA_OPTIONS)

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

    def configure_main(self):
        f = open(os.path.join(self.work_root, self.name+'.scr'),'w')

        (src_files, incdirs) = self._get_fileset_files()
        for key, value in self.vlogdefine.items():
            f.write('+define+{}={}\n'.format(key, self._param_value_str(value, '')))

        for key, value in self.vlogparam.items():
            f.write('+parameter+{}.{}={}\n'.format(self.toplevel, key, self._param_value_str(value, '"')))
        for id in incdirs:
            f.write("+incdir+" + id+'\n')
        timescale = self.tool_options.get('timescale')
        if timescale:
            with open(os.path.join(self.work_root, 'timescale.v'), 'w') as tsfile:
                tsfile.write("`timescale {}\n".format(timescale))
            f.write('timescale.v\n')
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
            f.write("IVERILOG_OPTIONS := {}\n".format(' '.join(self.tool_options.get('iverilog_options', []))))
            if self.plusarg:
                plusargs = []
                for key, value in self.plusarg.items():
                    plusargs += ['+{}={}'.format(key, self._param_value_str(value))]
                f.write("EXTRA_OPTIONS    ?= {}\n".format(' '.join(plusargs)))

            f.write(self.MAKEFILE_TEMPLATE)

            for vpi_module in self.vpi_modules:
                _incs = ['-I' + s for s in vpi_module['include_dirs']]
                _libs = ['-l'+l for l in vpi_module['libs']]
                _srcs = vpi_module['src_files']
                f.write(self.VPI_MAKE_SECTION.format(name = vpi_module['name'],
                                                     libs = ' '.join(_libs),
                                                     incs = ' '.join(_incs),
                                                     srcs = ' '.join(_srcs)))

    def run_main(self):
        args = ['run']

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ['+{}={}'.format(key, self._param_value_str(value))]
            args.append('EXTRA_OPTIONS='+' '.join(plusargs))

        self._run_tool('make', args)
