#FIXME: Add IP-XACT support
import importlib
import logging
import os
from pyparsing import Forward, OneOrMore, Optional, Suppress, Word, alphanums
import shutil
import yaml

from ipyxact.ipyxact import Component
from fusesoc import utils
from fusesoc.vlnv import Vlnv

logger = logging.getLogger(__name__)

class File(object):
    def __init__(self, tree):
        self.copyto = ""
        self.file_type = ''
        self.is_include_file = False
        self.logical_name = ''
        if type(tree) is dict:
            for k, v in tree.items():
                self.name = k
                if 'file_type' in v:
                    self.file_type = v['file_type']
                if 'is_include_file' in v:
                    self.is_include_file = v['is_include_file']
                if 'copyto' in v:
                    self.copyto = v['copyto']
        else:
            self.name = tree
            self.is_include_file = False #"FIXME"

class String(str):
    def parse(self, flags):
        _flags = []
        for k,v in flags.items():
            if v == True:
                _flags.append(k)
            elif v in [False, None]:
                pass
            else:
                _flags.append(k+'_'+v)

        def cb_conditional(s,l,t):
            if (t.cond in _flags) != (t.negate == '!'):
                return t.expr
            else:
                return []
        word = Word(alphanums+':>.[]_-,=~/')
        conditional = Forward()
        conditional << (Optional("!")("negate") + word("cond") + Suppress('?') + Suppress('(') + OneOrMore(conditional ^ word)("expr") + Suppress(')')).setParseAction(cb_conditional)
        #string = (function ^ word)
        string = word
        string_list = OneOrMore(conditional ^ string)
        s = ' '.join(string_list.parseString(self.__str__()))
        logger.debug("Parsing '{}' with flags {} => {}".format(self.__str__(),
                                                               str(_flags),s))
        return s

class Section(object):
    members = {}
    lists   = {}
    dicts   = {}
    def __init__(self, tree):
        for k, v in tree.items():
            if not v:
                continue
            if k in self.members:
                setattr(self, k, globals()[self.members[k]](v))
            elif k in self.lists:
                _l = []
                for _item in v:
                    try:
                        _l.append(globals()[self.lists[k]](_item))
                    except TypeError as e:
                        raise SyntaxError("Bad option '{}' in section '{}'".format(_item, k))
                setattr(self, k, _l)
            elif k in self.dicts:
                if not isinstance(v, dict):
                    raise SyntaxError("Object in '{}' section must be a dict".format(k))
                _d = {}
                for _name, _items in v.items():
                    try:
                        _d[_name] = globals()[self.dicts[k]](_items)
                    except AttributeError as e:
                        raise SyntaxError("Bad option '{}' in section '{}'".format(_name, k))
                setattr(self, k, _d)
            else:
                raise KeyError(k + " in section " + self.__class__.__name__)

class Provider(object):
    def __new__(cls, *args, **kwargs):
        provider_name = args[0]['name']
        if provider_name is None:
            raise RuntimeError('Missing "name" in section [provider]')
        provider_module = importlib.import_module(
            'fusesoc.provider.%s' % provider_name)
        return provider_module.PROVIDER_CLASS(args[0],
                                              "FIXME: core_root is used by local providers",
                                             "FIXME: cache_root can be set in fetch call")

class Core:
    def __init__(self, core_file, cache_root, build_root):
        basename = os.path.basename(core_file)

        self.core_root = os.path.dirname(core_file)

        try:
            _root = Root(yaml.load(open(core_file)))
        except KeyError as e:
            raise SyntaxError("Unknown item {}".format(e))
        except (yaml.scanner.ScannerError, yaml.constructor.ConstructorError) as e:
            raise SyntaxError(str(e))
        for i in _root.members:
            setattr(self, i, getattr(_root, i))
        for i in _root.lists:
            setattr(self, i, getattr(_root, i))
        for i in _root.dicts:
            setattr(self, i, getattr(_root, i))

        self.export_files = []
        if not self.name:
            raise SyntaxError("Missing 'name' parameter")
        self.sanitized_name = self.name.sanitized_name

        for fs in self.filesets.values():
            if fs.file_type:
                for f in fs.files:
                    if not f.file_type:
                        f.file_type = str(fs.file_type)
            if fs.logical_name:
                for f in fs.files:
                    if not f.logical_name:
                        f.logical_name = str(fs.logical_name)
        for p in self.parameters.values():
            p.datatype    = str(p.datatype)
            p.default     = str(p.default) if p.default else ''
            p.description = str(p.description)
            p.paramtype   = str(p.paramtype)

        for k, v in self.targets.items():
            setattr(v, 'name', k)


        if self.provider:
            self.files_root = os.path.join(cache_root,
                                           self.sanitized_name)
            #Ugly hack. Don't like injecting vars
            #How about a setup function or setters?
            self.provider.core_root  = self.core_root
            self.provider.files_root = self.files_root
        else:
            self.files_root = self.core_root

        self.scripts = [] #FIXME

    def cache_status(self):
        if self.provider:
            return self.provider.status()
        else:
            return 'local'

    def export(self, dst_dir, flags={}):
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)

        src_files = [f.name for f in self.get_files(flags)]


        for k, v in self._get_vpi(flags).items():
            src_files += [f.name for f in v['src_files'] + v['inc_files']] #FIXME include files
        self._debug("Exporting {}".format(str(src_files)))

        #for fs in self._get_filesets(flags):
        #    src_files += [f.name for f in fs.files]
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

    def get_scripts(self, flags):
        return {} #FIXME

    def get_tool(self, flags):
        self._debug("Getting tool for flags {}".format(str(flags)))
        tool = None
        if flags['tool']:
            tool = flags['tool']
        else:
            _flags = flags.copy()
            _flags['is_toplevel'] = True
            target = self._get_target(_flags)
            if target and target.default_tool:
                tool = target.default_tool

        if tool:
            self._debug(" Matched tool {}".format(tool))
        else:
            self._debug(" Matched no tool")
        return tool

    def get_tool_options(self, flags):
        _flags = flags.copy()

        self._debug("Getting tool options for flags {}".format(str(_flags)))
        target = self._get_target(_flags)
        section = None
        try:
            section = getattr(target.tools, flags['tool'])
        except AttributeError:
            pass

        options = {}
        if section:
            for member in section.members:
                if hasattr(section, member):
                    _member = getattr(section, member)
                    if _member:
                        options[member] = _member
            for member in section.lists:
                if hasattr(section, member):
                    _member = getattr(section, member)
                    if _member:
                        options[member] = [str(x) for x in _member]
        self._debug("Found tool options {}".format(str(options)))
        return options

    def get_depends(self, flags): #Add use flags?
        depends = []
        self._debug("Getting dependencies for flags {}".format(str(flags)))
        for fs in self._get_filesets(flags):
            depends += [Vlnv(d) for d in self._parse_list(flags, fs.depend)]
        return depends

    def get_files(self, flags):
        src_files = []
        for fs in self._get_filesets(flags):
            src_files += fs.files
        return src_files

    def get_parameters(self, flags={}):
        self._debug("Getting parameters for flags '{}'".format(str(flags)))
        target = self._get_target(flags)
        parameters = []

        if target:
            for p in self._parse_list(flags, target.parameters):
                _p = self.parameters[p]
                _p.name = p
                parameters.append(_p)
        self._debug("Found parameters {}".format(parameters))
        return parameters

    def get_toplevel(self, flags):
        _flags = flags.copy()
        _flags['is_toplevel'] = True #FIXME: Is this correct?
        self._debug("Getting toplevel for flags {}".format(str(_flags)))
        target = self._get_target(_flags)
        if target.toplevel:
            toplevel = self._parse_list(_flags, target.toplevel)
            self._debug("Matched toplevel {}".format(toplevel))
            return ' '.join(toplevel)
        else:
            s = "{} : Target '{}' has no toplevel"
            raise SyntaxError(s.format(self.name, target.name))

    def get_work_root(self, flags):
        _flags = flags.copy()
        _flags['is_toplevel'] = True
        return self._get_target(_flags).name+'-'+flags['tool']

    def _get_vpi(self, flags):
        vpi = {}
        target = self._get_target(flags)
        if not target:
            return vpi
        for vpi_name in self._parse_list(flags, target.vpi):
            vpi_lib = self.vpi[vpi_name]
            files = []
            incfiles = [] #Really do this automatically?
            for fs in vpi_lib.filesets:
                for f in self.filesets[fs].files:
                    if f.is_include_file:
                        incfiles.append(f)
                    else:
                        files.append(f)
            vpi[vpi_name] = {'src_files' : files,
                             'inc_files' : incfiles,
                             'libs'      : [str(l) for l in vpi_lib.libs]}
        return vpi

    def get_vpi(self, flags):
        self._debug("Getting VPI libraries for flags {}".format(flags))
        target = self._get_target(flags)
        vpi = []
        _vpi = self._get_vpi(flags)
        self._debug(" Matched VPI libraries {}".format([v for v in _vpi]))
        for k, v in _vpi.items():
            vpi.append({'name'         : k,
                        'src_files'    : v['src_files'],
                        'include_dirs' : utils.unique_dirs(v['inc_files']),
                        'libs'         : v['libs'],
            })
        return vpi

    def info(self):
        s = """CORE INFO
Name:                   {}
Core root:              {}

File sets:
{}
"""
        return s.format(str(self.name),
                        str(self.core_root),
                        "FIXME")
        #FIXME: Start from root and recursively go down the tree
        filesets = ""
        for k,v in self.filesets.items():
            print("""
 Name  : {}
 Files :""".format(k))
            if not v.files:
                print(" <No files>")
            else:
                _longest_name = max([len(x.name) for x in v.files])
                _longest_type = max([len(x.file_type) for x in v.files])
                for f in v.files:
                    print("  {} {} {}".format(f.name.ljust(_longest_name),
                                              f.file_type.ljust(_longest_type),
                                              "(include file)" if f.is_include_file else ""))
        print("Targets")
        print("=======")
        for target in self.targets:
            print(target)
        print("=======")

    def patch(self, dst_dir):
        #FIXME: Use native python patch instead
        patches = self.provider.patches
        for f in patches:
            patch_file = os.path.abspath(os.path.join(self.core_root, f))
            if os.path.isfile(patch_file):
                self._debug("  applying patch file: " + patch_file + "\n" +
                             "                   to: " + os.path.join(dst_dir))
                try:
                    utils.Launcher('git', ['apply', '--unsafe-paths',
                                     '--directory', os.path.join(dst_dir),
                                     patch_file]).run()
                except OSError:
                    print("Error: Failed to call external command 'patch'")
                    return False
        return True

    def setup(self):
        if self.provider:
            if self.provider.fetch():
                self.patch(self.files_root)

    def _debug(self, msg):
        logger.debug("{} : {}".format(str(self.name), msg))

    def _get_target(self, flags):
        self._debug(" Resolving target for flags '{}'".format(str(flags)))

        target_name = None
        if 'is_toplevel' in flags and flags['is_toplevel']:
            if 'target' in flags and flags['target']:
                target_name = flags['target']
            else:
                target_name = "default"
        else:
            target_name = "default"

        if target_name in self.targets:
            self._debug(" Matched target {}".format(target_name))
            return self.targets[target_name]
        else:
            raise SyntaxError("Could not find target '{}' in {}".format(target_name, self.name))

    def _get_filesets(self, flags):
        self._debug("Getting filesets for flags '{}'".format(str(flags)))
        target = self._get_target(flags)
        if not target:
            return []
        filesets = []

        for fs in self._parse_list(flags, target.filesets):
            if not fs in self.filesets:
                raise SyntaxError("Fileset '{}', requested by fileset '{}', was not found".format(_fs, target.name))
            filesets.append(self.filesets[fs])

        self._debug(" Matched filesets {}".format(target.filesets))
        return filesets

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

    def _parse_list(self, flags, l):
        r = []
        for x in l:
            _x = x.parse(flags)
            if _x:
                r.append(_x)
        return r
    #return [x.parse(flags) for x in l if x.parse(flags)]
description = """
---
Root:
  members:
    name        : Vlnv
    description : String
    provider    : Provider
    CAPI=2      : String
    scripts     : Scripts
  dicts:
    filesets   : Fileset
    targets    : Target
    parameters : Parameter
    vpi        : Vpi

Fileset:
  members:
    file_type    : String
    logical_name : String
  lists:
    files      : File
    depend     : String

Target:
  members:
    default_tool : String
    tools    : Tools
  lists:
    filesets   : String
    flags      : String #FIXME
    parameters : String
    toplevel   : String
    vpi        : String

Tools:
  members:
    icarus    : Icarus
    modelsim  : Modelsim
    quartus   : Quartus
    verilator : Verilator

Parameter:
  members:
    datatype : String
    default  : String
    description : String
    paramtype   : String
    scope       : String

Icarus:
  lists:
    iverilog_options : String

Quartus:
  members:
    family          : String
    device          : String
  lists:
    quartus_options : String

Modelsim:
  lists:
    vlog_options    : String
    vsim_options    : String

Verilator:
  members:
    mode              : String
  lists:
    libs              : String
    verilator_options : String

Scripts:
  lists:
    pre_build  : String
    post_build : String
    pre_run    : String
    post_run   : String
Vpi:
  lists:
    libs         : String
    filesets : String

"""

def _generate_classes(j, base_class):
    for cls, _items in j.items():
        class_members = {}
        if 'members' in _items:
            for key in _items['members']:
                class_members[key] = None
            class_members['members'] = _items['members']
        if 'lists' in _items:
            for key in _items['lists']:
                class_members[key] = []
            class_members['lists'] = _items['lists']
        if 'dicts' in _items:
            for key in _items['dicts']:
                class_members[key] = {}
            class_members['dicts'] = _items['dicts']

        generatedClass = type(cls, (base_class,), class_members)
        globals()[generatedClass.__name__] = generatedClass

_generate_classes(yaml.load(description), Section)
