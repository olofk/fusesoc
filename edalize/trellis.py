import os.path

from edalize.edatool import Edatool

class Trellis(Edatool):

    tool_options = {
        'lists' : {
            'nextpnr_options'     : 'String',
            'yosys_synth_options' : 'String',
        }
    }

    argtypes = ['vlogdefine', 'vlogparam']

    def configure_main(self):
        # Write yosys script file
        (src_files, incdirs) = self._get_fileset_files()
        with open(os.path.join(self.work_root, self.name+'.ys'), 'w') as yosys_file:
            for key, value in self.vlogdefine.items():
                yosys_file.write("verilog_defines -D{}={}\n".format(key, self._param_value_str(value)))

            yosys_file.write("verilog_defaults -push\n")
            yosys_file.write("verilog_defaults -add -defer\n")
            if incdirs:
                yosys_file.write("verilog_defaults -add {}\n".format(' '.join(['-I'+d for d in incdirs])))

            for f in src_files:
                if f.file_type in ['verilogSource']:
                    yosys_file.write("read_verilog {}\n".format(f.name))
                elif f.file_type == 'user':
                    pass
            for key, value in self.vlogparam.items():
                _s = "chparam -set {} {} $abstract\{}\n"
                yosys_file.write(_s.format(key,
                                           self._param_value_str(value, '"'),
                                           self.toplevel))

            yosys_file.write("verilog_defaults -pop\n")
            yosys_file.write("synth_ecp5 -nomux")
            yosys_synth_options = self.tool_options.get('yosys_synth_options', [])
            for option in yosys_synth_options:
                yosys_file.write(' ' + option)
            yosys_file.write(" -json {}.json".format(self.name))
            if self.toplevel:
                yosys_file.write(" -top " + self.toplevel)
            yosys_file.write("\n")

        # Write Makefile
        nextpnr_options     = self.tool_options.get('nextpnr_options', [])
        template_vars = {
            'name'                : self.name,
            'nextpnr_options'     : nextpnr_options,
        }
        self.render_template('trellis-makefile.j2',
                             'Makefile',
                             template_vars)
