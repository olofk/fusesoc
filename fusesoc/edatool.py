import argparse
from collections import OrderedDict
import os
import subprocess
import logging
import yaml

from fusesoc.utils import Launcher
logger = logging.getLogger(__name__)

class FileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        path = os.path.expandvars(values[0])
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        setattr(namespace, self.dest, [path])

class EdaTool(object):

    def __init__(self, eda_api_file, work_root):
        eda_api = yaml.load(open(eda_api_file))
        self.name = eda_api['name']
        _tool_name = self.__class__.__name__.lower()
        self.tool_options = eda_api['tool_options'][_tool_name]
        self.fusesoc_options = eda_api['tool_options']['fusesoc']

        self.work_root = work_root
        self.env = os.environ.copy()

        self.env['WORK_ROOT'] = os.path.abspath(self.work_root)

        self.plusarg     = OrderedDict()
        self.vlogparam   = OrderedDict()
        self.vlogdefine  = OrderedDict()
        self.generic     = OrderedDict()
        self.cmdlinearg  = OrderedDict()
        self.parsed_args = False

        self.files      = eda_api['files']
        self.parameters = eda_api['parameters']
        self.toplevel = eda_api['toplevel']
        self.vpi_modules = eda_api['vpi']

    def build(self):
        self.build_pre()
        self.build_main()
        self.build_post()

    def build_pre(self):
        if 'pre_build_scripts' in self.fusesoc_options:
            self._run_scripts(self.fusesoc_options['pre_build_scripts'])

    def build_main(self):
        Launcher('make', cwd=self.work_root).run()

    def build_post(self):
        if 'post_build_scripts' in self.fusesoc_options:
            self._run_scripts(self.fusesoc_options['post_build_scripts'])

    def parse_args(self, args, prog, paramtypes):
        if self.parsed_args:
            return
        typedict = {'bool' : {'action' : 'store_true'},
                    'file' : {'type' : str , 'nargs' : 1, 'action' : FileAction},
                    'int'  : {'type' : int , 'nargs' : 1},
                    'str'  : {'type' : str , 'nargs' : 1},
                    }
        progname = 'fusesoc {} {}'.format(prog,
                                          self.name)
        parser = argparse.ArgumentParser(prog = progname,
                                         conflict_handler='resolve')
        param_groups = {}
        _descr = {'plusarg'    : 'Verilog plusargs (Run-time option)',
                  'vlogparam'  : 'Verilog parameters (Compile-time option)',
                  'vlogdefine' : 'Verilog defines (Compile-time global symbol)',
                  'generic'    : 'VHDL generic (Run-time option)',
                  'cmdlinearg' : 'Command-line arguments (Run-time option)'}
        param_type_map = {}

        for param in self.parameters:
            _paramtype = param['paramtype']
            if _paramtype in paramtypes:
                if not _paramtype in param_groups:
                    param_groups[_paramtype] = \
                    parser.add_argument_group(_descr[_paramtype])

                default = None
                if param['default']:
                    try:
                        default = [typedict[param['datatype']]['type'](param['default'])]
                    except KeyError as e:
                        pass
                try:
                    param_groups[_paramtype].add_argument('--'+param['name'],
                                                               help=param['description'],
                                                               default=default,
                                                               **typedict[param['datatype']])
                except KeyError as e:
                    raise RuntimeError("Invalid data type {} for parameter '{}'".format(str(e),
                                                                                        param['name']))
                param_type_map[param['name'].replace('-','_')] = _paramtype
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

    def _get_fileset_files(self, force_slash=False):
        class File:
            def __init__(self, name, file_type, logical_name):
                self.name         = name
                self.file_type    = file_type
                self.logical_name = logical_name
        incdirs = []
        src_files = []
        for f in self.files:
            if f['is_include_file']:
                _incdir = os.path.dirname(f['name'])
                if force_slash:
                    _incdir = _incdir.replace('\\', '/')
                if not _incdir in incdirs:
                    incdirs.append(_incdir)
            else:
                _name = f['name']
                if force_slash:
                    _name = _name.replace('\\', '/')
                src_files.append(File(_name,
                                      f['file_type'],
                                      f['logical_name']))
        return (src_files, incdirs)

    """ Convert a parameter value to string suitable to be passed to an EDA tool

    Rules:
    - Booleans are represented as 0/1
    - Strings are either passed through (strings_in_quotes=False) or
      put into double quotation marks (")
    - Everything else (including int, float, etc.) are converted using the str()
      function.
    """
    def _param_value_str(self, param_value, strings_in_quotes=False):

      if type(param_value) == bool:
          if (param_value) == True:
              return '1'
          else:
              return '0'
      elif type(param_value) == str:
          if strings_in_quotes:
              return '"'+str(param_value)+'"'
          else:
              return str(param_value)
      else:
          return str(param_value)

    def _run_scripts(self, scripts):
        for script in scripts:
            for cmd, options in script.items():
                if not (os.path.isfile(cmd) and os.access(cmd, os.X_OK)):
                    raise RuntimeError("'{}' is not an executable file".format(cmd))
                _env = self.env.copy()
                if 'env' in options:
                    _env.update(options['env'])
                logger.info("Running " + cmd);
                try:
                    subprocess.check_call([cmd],
                                          cwd = self.work_root,
                                          env = _env,
                                          shell=True)
                except subprocess.CalledProcessError as e:
                    msg = "'{}' exited with error code {}"
                    raise RuntimeError(msg.format(cmd, e.returncode))
