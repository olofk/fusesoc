import logging
import os.path
import platform
import re

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

""" Synopsys (formerly Atrenta) Spyglass Backend

Spyglass performs static source code analysis on HDL code and checks for common
coding errors or coding style violations.

Example snippet of a CAPI2 description file:

spyglass:
  methodology: "GuideWare/latest/block/rtl_handoff"
  goals:
    - lint/lint_rtl
  spyglass_options:
    # prevent error SYNTH_5273 on generic RAM descriptions
    - handlememory yes

"""
class Spyglass(Edatool):

    tool_options = {
        'members' : {
            'methodology' : 'String'
        },
        'lists': {
            'goals': 'String',
            'spyglass_options': 'String',
        },
    }

    argtypes = ['vlogdefine', 'vlogparam']

    tool_options_defaults = {
         'methodology': 'GuideWare/latest/block/rtl_handoff',
         'goals': [ 'lint/lint_rtl' ],
         'spyglass_options': [],
    }

    def _set_tool_options_defaults(self):
        for key, default_value in self.tool_options_defaults.items():
            if not key in self.tool_options:
                logger.info("Set Spyglass tool option %s to default value %s" 
                    % (key, str(default_value)))
                self.tool_options[key] = default_value


    """ Configuration is the first phase of the build

    This writes the project TCL files and Makefile. It first collects all
    sources, IPs and contraints and then writes them to the TCL file along
    with the build steps.
    """
    def configure_main(self):
        self._set_tool_options_defaults()

        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        self.jinja_env.filters['src_file_filter'] = self.src_file_filter

        has_systemVerilog = False
        for src_file in src_files:
            if src_file.file_type.startswith('systemVerilogSource'):
                has_systemVerilog = True
                break

        template_vars = {
            'name'              : self.name,
            'src_files'         : src_files,
            'incdirs'           : incdirs,
            'tool_options'      : self.tool_options,
            'toplevel'          : self.toplevel,
            'vlogparam'         : self.vlogparam,
            'vlogdefine'        : self.vlogdefine,
            'has_systemVerilog' : has_systemVerilog,
            'sanitized_goals'   : [],
        }

        self.render_template('spyglass-project.prj.j2',
                             self.name + '.prj',
                             template_vars)

        # Create a single TCL file for each goal
        goals = ['Design_Read'] + self.tool_options['goals']

        for goal in goals:
            template_vars['goal'] = goal
            sanitized_goal = re.sub(r"[^a-zA-Z0-9]", '_', goal).lower()
            template_vars['sanitized_goals'].append(sanitized_goal)

            self.render_template('spyglass-run-goal.tcl.j2',
                                 'spyglass-run-%s.tcl' % sanitized_goal,
                                 template_vars)


        self.render_template('Makefile.j2',
                             'Makefile',
                             template_vars)

    def src_file_filter(self, f):
        def _vhdl_source(f):
            s = 'read_file -type vhdl'
            if f.logical_name:
                s += ' -library '+f.logical_name
            return s

        file_types = {
            'verilogSource'       : 'read_file -type verilog',
            'systemVerilogSource' : 'read_file -type verilog',
            'vhdlSource'          : _vhdl_source(f),
            'tclSource'           : 'source',
            'waiver'              : 'read_file -type waiver',
        }
        _file_type = f.file_type.split('-')[0]
        if _file_type in file_types:
            return file_types[_file_type] + ' ' + f.name
        elif _file_type == 'user':
            return ''
        else:
            _s = "{} has unknown file type '{}'"
            logger.warning(_s.format(f.name,
                                     f.file_type))
        return ''
