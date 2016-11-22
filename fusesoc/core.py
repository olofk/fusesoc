from collections import OrderedDict
import importlib
import logging
import os
import shutil

from ipyxact.ipyxact import Component
from fusesoc import section
from fusesoc import utils
from fusesoc.config import Config
from fusesoc.fusesocconfigparser import FusesocConfigParser
from fusesoc.plusargs import Plusargs
from fusesoc.vlnv import Vlnv

logger = logging.getLogger(__name__)

class FileSet(object):
    def __init__(self, name="", file=[], usage = [], private=False):
        self.name    = name
        self.file    = file
        self.usage   = usage
        self.private = private

class OptionSectionMissing(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Core:
    def __init__(self, core_file):
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

        self.export_files = []

        config = FusesocConfigParser(core_file)

        #Add .system options to .core file
        system_file = os.path.join(self.core_root, basename.split('.core')[0]+'.system')
        if os.path.exists(system_file):
            self._merge_system_file(system_file, config)

        #FIXME : Make simulators part of the core object
        self.simulator        = config.get_section('simulator')

        for s in section.load_all(config, core_file):
            if type(s) == tuple:
                _l = getattr(self, s[0].TAG)
                _l[s[1]] = s[0]
                setattr(self, s[0].TAG, _l)
            else:
                setattr(self, s.TAG, s)

        if self.main.name:
            self.name = Vlnv(self.main.name)
        else:
            self.name = Vlnv(basename.split('.core')[0])

        self.sanitized_name = self.name.sanitized_name

        self.depend     = self.main.depend
        self.simulators = self.main.simulators

        self._collect_filesets()

        cache_root = os.path.join(Config().cache_root, self.sanitized_name)
        if config.has_section('plusargs'):
            utils.pr_warn("plusargs section is deprecated and will not be parsed by FuseSoC. Please migrate to parameters in " + str(self.name))
            self.plusargs = Plusargs(dict(config.items('plusargs')))
        if config.has_section('provider'):
            items    = dict(config.items('provider'))

            provider_name = items.get('name')
            if provider_name is None:
                raise RuntimeError('Missing "name" in section [provider]')
            try:
                provider_module = importlib.import_module(
                        'fusesoc.provider.%s' % provider_name)
                self.provider = provider_module.PROVIDER_CLASS(self.name,
                    items, self.core_root, cache_root)
            except ImportError:
                raise
        if self.provider:
            self.files_root = self.provider.files_root

        # We need the component file here, but it might not be
        # available until the core is fetched. Try to fetch first if any
        # of the component files are missing
        if False in [os.path.exists(f) for f in self.main.component]:
            self.setup()

        for f in self.main.component:
            self._parse_component(os.path.join(self.files_root, f))

        if self.main.backend:
            self.backend = getattr(self, self.main.backend)

    def cache_status(self):
        if self.provider:
            return self.provider.status()
        else:
            return 'local'

    def setup(self):
        if self.provider:
            if self.provider.fetch():
                self.patch(self.files_root)

    def export(self, dst_dir):
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)

        #FIXME: Separate tb_files to an own directory tree (src/tb/core_name ?)
        src_files = self.export_files

        for s in section.SECTION_MAP:
            obj = getattr(self, s)
            if obj:
                if not (type(obj) == OrderedDict):
                    src_files += [f.name for f in obj.export()]
                else:
                    for item in obj.values():
                        src_files += [f.name for f in item.export()]

        dirs = list(set(map(os.path.dirname,src_files)))
        for d in dirs:
            if not os.path.exists(os.path.join(dst_dir, d)):
                os.makedirs(os.path.join(dst_dir, d))

        for f in src_files:
            if not os.path.isabs(f):
                if(os.path.exists(os.path.join(self.core_root, f))):
                    shutil.copyfile(os.path.join(self.core_root, f),
                                    os.path.join(dst_dir, f))
                elif (os.path.exists(os.path.join(self.files_root, f))):
                    shutil.copyfile(os.path.join(self.files_root, f),
                                    os.path.join(dst_dir, f))
                else:
                    raise RuntimeError('Cannot find %s in :\n\t%s\n\t%s'
                                  % (f, self.files_root, self.core_root))

    def patch(self, dst_dir):
        #FIXME: Use native python patch instead
        patch_root = os.path.join(self.core_root, 'patches')
        patches = self.main.patches
        if os.path.exists(patch_root):
            for p in sorted(os.listdir(patch_root)):
                patches.append(os.path.join('patches', p))

        for f in patches:
            patch_file = os.path.abspath(os.path.join(self.core_root, f))
            if os.path.isfile(patch_file):
                logger.debug("  applying patch file: " + patch_file + "\n" +
                             "                   to: " + os.path.join(dst_dir))
                try:
                    utils.Launcher('git', ['apply', '--unsafe-paths',
                                     '--directory', os.path.join(dst_dir),
                                     patch_file]).run()
                except OSError:
                    print("Error: Failed to call external command 'patch'")
                    return False
        return True

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
        for section in ['icestorm', 'ise', 'quartus', 'vivado']:
            _replace(section)

        _replace('main', 'backend')
        _replace('scripts', 'pre_build_scripts' , 'pre_synth_scripts')
        _replace('scripts', 'post_build_scripts', 'post_impl_scripts')

    def _collect_filesets(self):

        self.file_sets = []

        if self.verilog:
            _files = []
            for f in self.verilog.include_files:
                if not f.file_type:
                    f.file_type = self.verilog.file_type
                f.is_include_file = True
                _files.append(f)
            for f in self.verilog.src_files:
                if not f.file_type:
                    f.file_type = self.verilog.file_type
                _files.append(f)

            self.file_sets.append(FileSet(name  = "verilog_src_files",
                                          file  = _files,
                                          usage = ['sim', 'synth']))

            _files = []
            for f in self.verilog.tb_include_files:
                if not f.file_type:
                    f.file_type = self.verilog.file_type
                    f.is_include_file = True
                _files.append(f)
            for f in self.verilog.tb_src_files:
                if not f.file_type:
                    f.file_type = self.verilog.file_type
                _files.append(f)
            self.file_sets.append(FileSet(name  = "verilog_tb_src_files",
                                          file  = _files,
                                          usage = ['sim']))

            _files = []
            for f in self.verilog.tb_private_src_files:
                if not f.file_type:
                    f.file_type = self.verilog.file_type
                _files.append(f)
            self.file_sets.append(FileSet(name    = "verilog_tb_private_src_files",
                                          file    = _files,
                                          usage   = ['sim'],
                                          private = True))
        for k, v in self.fileset.items():
            self.file_sets.append(FileSet(name = k,
                                          file = v.files,
                                          usage = v.usage,
                                          private = (v.scope == 'private')))

    def _parse_component(self, component_file):
        component = Component()
        component.load(component_file)

        if not self.main.description:
            self.main.description = component.description

        _file_sets = []
        for file_set in component.fileSets.fileSet:
            _name = file_set.name
            for f in file_set.file:
                self.export_files.append(f.name)
                #FIXME: Harmonize underscore vs camelcase
                f.file_type = f.fileType
                if f.isIncludeFile == 'true':
                    f.is_include_file = True
                else:
                    f.is_include_file = False
                f.logical_name = f.logicalName
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

        show_list = lambda l: "\n                        ".join([str(x) for x in l])
        show_dict = lambda d: show_list(["%s: %s" % (k, d[k]) for k in d.keys()])

        print("CORE INFO")
        print("Name:                   " + str(self.name))
        print("Core root:              " + self.core_root)
        if self.simulators:
            print("Supported simulators:   " + show_list(self.simulators))
        if self.plusargs: 
            print("\nPlusargs:               " + show_dict(self.plusargs.items))
        if self.depend:
            print("\nCommon dependencies : " + ' '.join([x.depstr() for x in self.depend]))
        for s in section.SECTION_MAP:
            if s in ['main', 'verilog']:
                continue
            obj = getattr(self, s)
            if obj:
                print("== " + s + " ==")
                if(type(obj) == OrderedDict):
                    for k, v in obj.items():
                        print(str(k))
                else:
                    print(obj)
        print("File sets:")
        for s in self.file_sets:
            print("""
 Name  : {}
 Scope : {}
 Usage : {}
 Files :""".format(s.name, "private" if s.private else "public", '/'.join(s.usage)))
            if not s.file:
                print(" <No files>")
            else:
                _longest_name = max([len(x.name) for x in s.file])
                _longest_type = max([len(x.file_type) for x in s.file])
                for f in s.file:
                    print("  {} {} {}".format(f.name.ljust(_longest_name),
                                              f.file_type.ljust(_longest_type),
                                              f.is_include_file))
