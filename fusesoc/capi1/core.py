from collections import OrderedDict
import importlib
import logging
import os
import shutil

from ipyxact.ipyxact import Component
from fusesoc import utils
from fusesoc.provider import get_provider
from fusesoc.vlnv import Vlnv
from fusesoc.capi1 import section
from fusesoc.capi1.fusesocconfigparser import FusesocConfigParser
from fusesoc.capi1.plusargs import Plusargs

logger = logging.getLogger(__name__)

class FileSet(object):
    def __init__(self, name="", file=[], usage = [], private=False):
        self.name    = name
        self.file    = file
        self.usage   = usage
        self.private = private

    def __str__(self):
        s = """Name  : {}
 Scope : {}
 Usage : {}
 Files :\n""".format(self.name,
                     "private" if self.private else "public",
                     '/'.join(self.usage))
        if not self.file:
            s += " <No files>\n"
        else:
            _longest_name = max([len(x.name) for x in self.file])
            _longest_type = max([len(x.file_type) for x in self.file])
            for f in self.file:
                _s = "  {} {} {}\n"
                s += _s.format(f.name.ljust(_longest_name),
                               f.file_type.ljust(_longest_type),
                               "(include file)" if f.is_include_file else "")
        return s

class Core:
    def __init__(self, core_file, cache_root='', build_root=''):
        basename = os.path.basename(core_file)
        self.depend = []
        self.simulators = []

        self.plusargs = None
        self.provider = None
        self.backend  = None

        for s in section.SECTION_MAP:
            assert(not hasattr(self, s))
            if(section.SECTION_MAP[s].named):
                setattr(self, s, OrderedDict())
            else:
                setattr(self, s, None)

        self.core_root = os.path.dirname(core_file)
        self.files_root = self.core_root
        self.build_root = build_root

        self.export_files = []

        config = FusesocConfigParser(core_file)

        #Add .system options to .core file
        system_file = os.path.join(self.core_root, basename.split('.core')[0]+'.system')
        if os.path.exists(system_file):
            self._merge_system_file(system_file, config)

        #FIXME : Make simulators part of the core object
        self.simulator        = config.get_section('simulator')
        if not 'toplevel' in self.simulator:
            self.simulator['toplevel'] = 'orpsoc_tb'

        for s in section.load_all(config, core_file):
            if type(s) == tuple:
                _l = getattr(self, s[0].TAG)
                _l[s[1]] = s[0]
                setattr(self, s[0].TAG, _l)
            else:
                setattr(self, s.TAG, s)

        if not self.main:
            self.main = section.MainSection()
        if self.main.name:
            self.name = Vlnv(self.main.name)
        else:
            self.name = Vlnv(basename.split('.core')[0])

        self.sanitized_name = self.name.sanitized_name

        self.depend     = self.main.depend[:]

        self.simulators = self.main.simulators

        if self.main.backend:
            try:
                self.backend = getattr(self, self.main.backend)
            except AttributeError:
                raise SyntaxError('Invalid backend "{}"'.format(self.main.backend))

        self._collect_filesets()

        cache_root = os.path.join(cache_root, self.sanitized_name)
        if config.has_section('plusargs'):
            self._warning("plusargs section is deprecated and will not be parsed by FuseSoC. Please migrate to parameters")
            self.plusargs = Plusargs(dict(config.items('plusargs')))
        if config.has_section('verilator') and config.has_option('verilator', 'define_files'):
            self._warning("verilator define_files are deprecated")
        if config.has_section('provider'):
            items    = dict(config.items('provider'))
            patch_root = os.path.join(self.core_root, 'patches')
            patches = self.main.patches
            if os.path.exists(patch_root):
                for p in sorted(os.listdir(patch_root)):
                    patches.append(os.path.join('patches', p))
            items['patches'] = patches
            provider_name = items.get('name')
            if provider_name is None:
                raise RuntimeError('Missing "name" in section [provider]')
            self.provider = get_provider(provider_name)(
                items, self.core_root, cache_root)
        if self.provider:
            self.files_root = self.provider.files_root

        # We need the component file here, but it might not be
        # available until the core is fetched. Try to fetch first if any
        # of the component files are missing
        if False in [os.path.exists(f) for f in self.main.component]:
            self.setup()

        for f in self.main.component:
            self._parse_component(f)

    def cache_status(self):
        if self.provider:
            return self.provider.status()
        else:
            return 'local'

    def get_depends(self, flags={}):
        self._debug("Getting dependencies for flags {}".format(str(flags)))
        _depends = self.depend
        try:
            _depends += getattr(self, flags['tool']).depend
        except (AttributeError, KeyError):
            pass
        return _depends

    def get_files(self, flags={}):
        files = []
        flow = self._get_flow(flags)
        usage = set([flow, flags['tool']])

        for fs in self.file_sets:
            if (not fs.private or flags['is_toplevel']) and (usage & set(fs.usage)):
                files += fs.file
        return files

    def get_parameters(self, flags={}):
        self._debug("Getting parameters for flags '{}'".format(str(flags)))
        parameters = {}
        for k, v in self.parameter.items():
            if (v.scope == 'public') or flags['is_toplevel']:
                parameters[k] = {'datatype'  : v.datatype,
                                 'paramtype' : v.paramtype}
                for field in ['default','description']:
                    if getattr(v, field):
                        parameters[k][field] = getattr(v, field)
        self._debug("Found parameters {}".format(parameters))
        return parameters

    def get_scripts(self, files_root, flags):
        def _build_dict(v, env):
            return [{'name' : x, 'cmd' : ['sh', os.path.join(files_root, x)], 'env' : env} for x in v]
        scripts = {}
        if self.scripts:
            env = {'BUILD_ROOT' : self.build_root,
                   'FILES_ROOT' : files_root,
            }
            flow = self._get_flow(flags)
            if flow is 'sim':
                for s in ['pre_build_scripts', 'pre_run_scripts', 'post_run_scripts']:
                    v = getattr(self.scripts, s)
                    if v:
                        scripts[s[0:-8]] = _build_dict(v, env)
            #For backwards compatibility we only use the script from the
            #top-level core in synth flows. We also rename them here to match
            #the backend stages and set the SYSTEM_ROOT env var
            elif flow is 'synth' and flags['is_toplevel']:
                env['SYSTEM_ROOT'] = self.files_root
                v = self.scripts.pre_synth_scripts
                if v:
                    scripts['pre_build'] = _build_dict(v, env)
                v = self.scripts.post_impl_scripts
                if v:
                    scripts['post_build'] = _build_dict(v, env)
        return scripts

    def get_toplevel(self, flags={}):
        self._debug("Getting toplevel for flags {}".format(str(flags)))
        if flags['tool'] == 'verilator':
            toplevel = self.verilator.top_module
        elif self.backend and self._get_flow(flags) == 'synth':
            toplevel = self.backend.top_module
        elif 'testbench' in flags and flags['testbench']:
            toplevel = flags['testbench']
        else:
            toplevel = self.simulator['toplevel']
        self._debug("Matched toplevel {}".format(toplevel))
        return toplevel

    def get_tool(self, flags):
        self._debug("Getting tool for flags {}".format(str(flags)))
        tool = None
        flow = self._get_flow(flags)
        if flags['tool']:
            tool =  flags['tool']
        elif flags['target'] == 'synth':
            if hasattr(self.main, 'backend'):
                tool = self.main.backend
        else:
            if len(self.simulators) > 0:
                tool = self.simulators[0]
        self._debug(" Matched tool {}".format(tool))
        return tool

    def get_tool_options(self, flags):
        self._debug("Getting tool options for flags {}".format(str(flags)))
        options = {}
        if hasattr(self, flags['tool']):
            section = getattr(self, flags['tool'])
        else:
            self._debug("CAPI1 does not support tool '{}'".format(flags['tool']))
            section = None

        if section:

            #Special cases for verilator
            if flags['tool'] == 'verilator':
                #Pick up verilator libs from all dependencies
                options['libs'] = section.libs

                #Set the mode option
                if flags['is_toplevel']:
                    if self.verilator.source_type == 'systemC':
                        options['mode'] = 'sc'
                    else:
                        options['mode'] = 'cc'
                    del(self.verilator.source_type)

                if self.verilator.cli_parser == 'fusesoc':
                    self.verilator.cli_parser = 'managed'
                elif self.verilator.cli_parser == '':
                    self.verilator.cli_parser = 'passthrough'

            #Otherwise, only care about options from toplevel core
            if flags['is_toplevel']:

                #Special case for isim. isim_options are really fuse_options
                if flags['tool'] == 'isim':
                    section._members['fuse_options'] = section._members.pop('isim_options')
                    section.fuse_options = section.isim_options

                #Special case for xsim. xsim_options are really xelab_options
                #Also add flags that were previously hardcoded in the backend
                if flags['tool'] == 'xsim':
                    if 'xsim_options' in section._members:
                        section._members['xelab_options'] = section._members.pop('xsim_options')
                        section.xelab_options = ['--timescale 1ps/1ps',
                                                 '--debug typical']
                        section.xelab_options += section.xsim_options
                    
                for member in section._members:
                    if hasattr(section, member) and getattr(section, member) and not member == 'depend':
                        #Strip quoted strings
                        _member = getattr(section, member)
                        if (type(_member) == str) and _member.startswith('"') and _member.endswith('"'):
                            _member = _member[1:-1]
                        options[member] = _member
        self._debug("Found tool options {}".format(str(options)))
        return options

    def get_vpi(self, flags):
        self._debug("Getting VPI libraries for flags {}".format(flags))
        vpi = []
        if self.vpi:
            vpi.append({'name'         : self.sanitized_name,
                        'src_files'    : [f.name for f in self.vpi.src_files],
                        'include_dirs' : self.vpi.include_dirs,
                        'libs'         : [l[2:] for l in self.vpi.libs],
            })
        self._debug(" Matched VPI libraries {}".format([v['name'] for v in vpi]))
        return vpi

    def get_work_root(self, flags):
        if self._get_flow(flags) is 'synth':
            s = 'bld-'
        else:
            s = 'sim-'
        return s+flags['tool']

    def setup(self):
        if self.provider:
            self.provider.fetch()

    def export(self, dst_dir, flags={}):
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)


        src_files = [f.name for f in self.get_files(flags)]
        if self.vpi and flags['tool'] in ['icarus', 'modelsim', 'rivierapro']:
            src_files += [f.name for f in self.vpi.src_files + self.vpi.include_files]
        for section in self.get_scripts(dst_dir, flags).values():
            for script in section:
                src_files.append(script['name'])

        self._debug("Exporting {}".format(str(src_files)))

        dirs = list(set(map(os.path.dirname,src_files)))
        for d in dirs:
            if not os.path.exists(os.path.join(dst_dir, d)):
                os.makedirs(os.path.join(dst_dir, d))

        for f in src_files:
            if not os.path.isabs(f):
                if(os.path.exists(os.path.join(self.core_root, f))):
                    shutil.copy2(os.path.join(self.core_root, f),
                                    os.path.join(dst_dir, f))
                elif (os.path.exists(os.path.join(self.files_root, f))):
                    shutil.copy2(os.path.join(self.files_root, f),
                                    os.path.join(dst_dir, f))
                else:
                    raise RuntimeError('Cannot find %s in :\n\t%s\n\t%s'
                                  % (f, self.files_root, self.core_root))

    def _get_flow(self, flags):
        flow = None
        if 'tool' in flags:
            if flags['tool'] in ['ghdl', 'icarus', 'isim', 'modelsim', 'rivierapro', 'xsim', 'vcs']:
                flow = 'sim'
            elif flags['tool'] in ['icestorm', 'ise', 'quartus', 'verilator', 'vivado', 'spyglass', 'trellis']:
                flow = 'synth'
        elif 'target' in flags:
            if flags['target'] is 'synth':
                flow = 'synth'
            elif flags['target'] is 'sim':
                flow = 'sim'
        return flow

    def _merge_system_file(self, system_file, config):
        def _replace(sec, src=None, dst=None):
            if not system.has_section(sec):
                return

            if not config.has_section(sec):
                config.add_section(sec)

            if src:
                if system.has_option(sec, src):
                    items = [src]
                else:
                    items = []
            else:
                items = system.options(sec)

            for item in items:
                if dst:
                    _dst = dst
                else:
                    _dst = item
                if not config.has_option(sec, _dst):
                    config.set(sec, _dst, system.get(sec, item))

        system = FusesocConfigParser(system_file)
        for section in ['icestorm', 'ise', 'quartus', 'vivado', 'trellis']:
            _replace(section)

        _replace('main', 'backend')
        _replace('scripts', 'pre_build_scripts' , 'pre_synth_scripts')
        _replace('scripts', 'post_build_scripts', 'post_impl_scripts')

    def _collect_filesets(self):
        def _append_files(section, file_type, is_include_file=False):
            _files = []
            for f in section:
                if not f.file_type:
                    f.file_type = file_type
                f.is_include_file = is_include_file
                _files.append(f)
            return _files

        self.file_sets = []

        _v = self.verilog
        if _v:
            _files  = _append_files(_v.include_files, _v.file_type, True)
            _files += _append_files(_v.src_files, _v.file_type)
            self.file_sets.append(FileSet(name  = "verilog_src_files",
                                          file  = _files,
                                          usage = ['sim', 'synth']))

            _files  = _append_files(_v.tb_include_files, _v.file_type, True)
            _files += _append_files(_v.tb_src_files, _v.file_type)
            self.file_sets.append(FileSet(name  = "verilog_tb_src_files",
                                          file  = _files,
                                          usage = ['sim']))
            _files  = _append_files(_v.tb_private_src_files, _v.file_type)
            self.file_sets.append(FileSet(name    = "verilog_tb_private_src_files",
                                          file    = _files,
                                          usage   = ['sim'],
                                          private = True))


        for k, v in self.fileset.items():
            self.file_sets.append(FileSet(name = k,
                                          file = v.files,
                                          usage = v.usage,
                                          private = (v.scope == 'private')))

        _bname = self.main.backend
        _b = self.backend
        if _b and _bname in ['icestorm', 'ise', 'quartus', 'trellis']:
            _files = []
            if _bname == 'icestorm':
                _files += _append_files(_b.pcf_file, 'PCF')
                del(_b.pcf_file)
            elif _bname == 'ise':
                _files += _append_files(_b.tcl_files, 'tclSource')
                _files += _append_files(_b.ucf_files, 'UCF')
                del(_b.ucf_files)
            elif _bname == 'quartus':
                _files += _append_files(_b.qsys_files, 'QSYS')
                _files += _append_files(_b.sdc_files, 'SDC')
                _files += _append_files(_b.tcl_files, 'tclSource')
                del(_b.qsys_files)
                del(_b.sdc_files)
                del(_b.tcl_files)
            if _files:
                self.file_sets.append(FileSet(name = "backend_files",
                                              file = _files,
                                              usage = [_bname],
                                              private = True))
                self.export_files += [f.name for f in _files]
        if self.verilator:
            if self.verilator.source_type == 'CPP':
                _file_type = 'cppSource'
            elif self.verilator.source_type == 'systemC':
                _file_type = 'systemCSource'
            elif self.verilator.source_type == 'C':
                _file_type = 'cSource'
            else:
                raise RuntimeError("Invalid verilator file type '{}'".format(self.verilator.source_type))
            _files  = _append_files(self.verilator.src_files, _file_type)
            _files += _append_files(self.verilator.include_files, _file_type, True)
            del(self.verilator.src_files)
            self.file_sets.append(FileSet(name = "verilator_src_files",
                                          file = _files,
                                          usage = ['verilator']))
            self.export_files += [f.name for f in _files]

            _files  = _append_files(self.verilator.tb_toplevel, _file_type)
            self.file_sets.append(FileSet(name = "verilator_tb_toplevel",
                                          file = _files,
                                          usage = ['verilator'],
                                          private = True))
            del(self.verilator.tb_toplevel)
            self.export_files += [f.name for f in _files]

    def _debug(self, msg):
        logger.debug("{} : {}".format(str(self.name), msg))

    def _warning(self, msg):
        logger.warning("{} : {}".format(str(self.name), msg))

    def _parse_component(self, component_file):
        component_dir = os.path.dirname(component_file)
        component = Component()
        component.load(os.path.join(self.files_root, component_file))

        if not self.main.description:
            self.main.description = component.description

        _file_sets = []
        for file_set in component.fileSets.fileSet:
            _name = file_set.name
            for f in file_set.file:
                f.name = os.path.normpath(os.path.join(component_dir, f.name))
                self.export_files.append(f.name)
                #FIXME: Harmonize underscore vs camelcase
                f.file_type = f.fileType
                if f.isIncludeFile == 'true':
                    f.is_include_file = True
                else:
                    f.is_include_file = False
                f.logical_name = f.logicalName
                f.copyto = ""
            #FIXME: Handle duplicates. Resolution function? (merge/replace, prio ipxact/core)
            _taken = False
            for fs in self.file_sets:
                if fs.name == file_set.name:
                    _taken = True
            if not _taken:
                _file_sets.append(FileSet(name = file_set.name,
                                          file = file_set.file[:],
                                          usage = ['sim', 'synth']))
        self.file_sets += _file_sets
    def info(self):
        HEADER = """CORE INFO
Name                 : {}
Core root            : {}
Supported simulators : {}
Common dependencies  : {}\n\n"""

        s = HEADER.format(str(self.name),
                          self.core_root,
                          ' '.join(self.simulators),
                          ' '.join([x.depstr() for x in self.main.depend]))
        for sec in sorted(section.SECTION_MAP):
            if sec in ['main', 'verilog', 'fileset']:
                continue
            obj = getattr(self, sec)
            if obj:
                if(type(obj) == OrderedDict):
                    for k, v in obj.items():
                        s += "== {} {} ==\n{}\n".format(sec,k, v)
                else:
                    s += "== {} ==\n{}\n".format(sec, obj)
        s += "File sets:\n"
        for fs in self.file_sets:
            s += str(fs) + '\n'

        if self.main.backend:
            s += "\n== Backend {} ==\n{}\n".format(self.main.backend,
                                                   self.backend)
        return s
