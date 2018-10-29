import argparse
from collections import OrderedDict
import os
import subprocess
import logging
import sys
from jinja2 import Environment, PackageLoader

logger = logging.getLogger(__name__)

# Jinja2 tests and filters, available in all templates
def jinja_filter_param_value_str(value, str_quote_style=""):
    """ Convert a parameter value to string suitable to be passed to an EDA tool

    Rules:
    - Booleans are represented as 0/1
    - Strings are either passed through or enclosed in the characters specified
      in str_quote_style (e.g. '"' or '\\"')
    - Everything else (including int, float, etc.) are converted using the str()
      function.
    """
    if type(value) == bool:
        if (value) == True:
            return '1'
        else:
            return '0'
    elif type(value) == str:
        return str_quote_style + str(value) + str_quote_style
    else:
        return str(value)


class FileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        path = os.path.expandvars(values[0])
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        setattr(namespace, self.dest, [path])

class Edatool(object):

    def __init__(self, eda_api, work_root=None):
        _tool_name = self.__class__.__name__.lower()

        try:
            self.name = eda_api['name']
        except KeyError:
            raise RuntimeError("Missing required parameter 'name'")

        self.tool_options = eda_api.get('tool_options', {}).get(_tool_name, {})

        self.files       = eda_api.get('files', [])
        self.toplevel    = eda_api.get('toplevel', [])
        self.vpi_modules = eda_api.get('vpi', [])

        self.hooks       = eda_api.get('hooks', {})
        self.parameters  = eda_api.get('parameters', {})

        self.work_root = work_root
        self.env = os.environ.copy()

        self.env['WORK_ROOT'] = self.work_root

        self.plusarg     = OrderedDict()
        self.vlogparam   = OrderedDict()
        self.vlogdefine  = OrderedDict()
        self.generic     = OrderedDict()
        self.cmdlinearg  = OrderedDict()
        self.parsed_args = False

        self.jinja_env = Environment(
            loader = PackageLoader(__package__, 'templates'),
            trim_blocks = True,
            lstrip_blocks = True,
        )
        self.jinja_env.filters['param_value_str'] = jinja_filter_param_value_str

    def configure(self, args):
        logger.info("Setting up project")
        self.configure_pre(args)
        self.configure_main()
        self.configure_post()

    def configure_pre(self, args):
        self.parse_args(args, self.argtypes)

    def configure_main(self):
        pass

    def configure_post(self):
        pass

    def build(self):
        self.build_pre()
        self.build_main()
        self.build_post()

    def build_pre(self):
        if 'pre_build' in self.hooks:
            self._run_scripts(self.hooks['pre_build'])

    def build_main(self):
        logger.info("Building");
        self._run_tool('make')

    def build_post(self):
        if 'post_build' in self.hooks:
            self._run_scripts(self.hooks['post_build'])

    def run(self, args):
        logger.info("Running")
        self.run_pre(args)
        self.run_main()
        self.run_post()

    def run_pre(self, args):
        self.parse_args(args, self.argtypes)
        if 'pre_run' in self.hooks:
            self._run_scripts(self.hooks['pre_run'])

    def run_main(self):
        pass

    def run_post(self):
        if 'post_run' in self.hooks:
            self._run_scripts(self.hooks['post_run'])

    def parse_args(self, args, paramtypes):
        if self.parsed_args:
            return
        typedict = {'bool' : {'action' : 'store_true'},
                    'file' : {'type' : str , 'nargs' : 1, 'action' : FileAction},
                    'int'  : {'type' : int , 'nargs' : 1},
                    'str'  : {'type' : str , 'nargs' : 1},
                    }
        progname = os.path.basename(sys.argv[0]) + ' run {}'.format(self.name)

        parser = argparse.ArgumentParser(prog = progname,
                                         conflict_handler='resolve')
        param_groups = {}
        _descr = {'plusarg'    : 'Verilog plusargs (Run-time option)',
                  'vlogparam'  : 'Verilog parameters (Compile-time option)',
                  'vlogdefine' : 'Verilog defines (Compile-time global symbol)',
                  'generic'    : 'VHDL generic (Run-time option)',
                  'cmdlinearg' : 'Command-line arguments (Run-time option)'}
        param_type_map = {}

        for name, param in self.parameters.items():
            _description = param.get('description', "No description")
            _paramtype = param['paramtype']
            if _paramtype in paramtypes:
                if not _paramtype in param_groups:
                    param_groups[_paramtype] = \
                    parser.add_argument_group(_descr[_paramtype])

                default = None
                if not param.get('default') is None:
                    try:
                        if param['datatype'] == 'bool':
                            default = param['default']
                        else:
                            default = [typedict[param['datatype']]['type'](param['default'])]
                    except KeyError as e:
                        pass
                try:
                    param_groups[_paramtype].add_argument('--'+name,
                                                               help=_description,
                                                               default=default,
                                                               **typedict[param['datatype']])
                except KeyError as e:
                    raise RuntimeError("Invalid data type {} for parameter '{}'".format(str(e),
                                                                                        name))
                param_type_map[name.replace('-','_')] = _paramtype
        #Parse arguments
        for key,value in sorted(vars(parser.parse_args(args)).items()):

            paramtype = param_type_map[key]
            if value is None:
                continue

            if type(value) == bool:
                _value = value
            else:
                _value = value[0]

            getattr(self, paramtype)[key] = _value
        self.parsed_args = True

    def render_template(self, template_file, target_file, template_vars = {}):
        """
        Render a Jinja2 template for the backend

        The template file is expected in the directory templates/BACKEND_NAME.
        """
        template_dir = str(self.__class__.__name__).lower()
        template = self.jinja_env.get_template(os.path.join(template_dir, template_file))
        file_path = os.path.join(self.work_root, target_file)
        with open(file_path, 'w') as f:
            f.write(template.render(template_vars))

    def _get_fileset_files(self, force_slash=False):
        class File:
            def __init__(self, name, file_type, logical_name):
                self.name         = name
                self.file_type    = file_type
                self.logical_name = logical_name
        incdirs = []
        src_files = []
        for f in self.files:
            if 'is_include_file' in f and f['is_include_file']:
                _incdir = os.path.dirname(f['name']) or '.'
                if force_slash:
                    _incdir = _incdir.replace('\\', '/')
                if not _incdir in incdirs:
                    incdirs.append(_incdir)
            else:
                _name = f['name']
                if force_slash:
                    _name = _name.replace('\\', '/')
                file_type = f.get('file_type', '')
                logical_name = f.get('logical_name', '')
                src_files.append(File(_name,
                                      file_type,
                                      logical_name))
        return (src_files, incdirs)

    def _param_value_str(self, param_value, str_quote_style=""):
        return jinja_filter_param_value_str(param_value, str_quote_style)

    def _run_scripts(self, scripts):
        for script in scripts:
            _env = self.env.copy()
            if 'env' in script:
                _env.update(script['env'])
            logger.info("Running " + script['name'])
            try:
                subprocess.check_call(script['cmd'],
                                      cwd = self.work_root,
                                      env = _env)
            except subprocess.CalledProcessError as e:
                msg = "'{}' exited with error code {}"
                raise RuntimeError(msg.format(script['name'], e.returncode))

    def _run_tool(self, cmd, args=[]):
        logger.debug("Running " + cmd)
        logger.debug("args  : " + ' '.join(args))

        try:
            subprocess.check_call([cmd] + args,
                                  cwd = self.work_root,
                                  stdin=subprocess.PIPE),
        except FileNotFoundError:
            _s = "Command '{}' not found. Make sure it is in $PATH"
            raise RuntimeError(_s.format(cmd))
        except subprocess.CalledProcessError:
            _s = "'{}' exited with an error code"
            raise RuntimeError(_s.format(cmd))
