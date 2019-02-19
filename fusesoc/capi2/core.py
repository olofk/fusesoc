#FIXME: Add IP-XACT support
import logging
import os
from pyparsing import Forward, OneOrMore, Optional, Suppress, Word, alphanums
import shutil
import yaml

from fusesoc import utils
from fusesoc.provider import get_provider
from fusesoc.vlnv import Vlnv
from edalize import get_edatools

logger = logging.getLogger(__name__)

class File(object):
    def __init__(self, tree):
        self.copyto = ""
        self.file_type = ''
        self.is_include_file = False
        self.logical_name = ''
        if type(tree) is dict:
            for k, v in tree.items():
                self.name = os.path.expandvars(k)
                self.file_type       = v.get('file_type', '')
                self.is_include_file = v.get('is_include_file', False)
                self.copyto          = v.get('copyto', '')
        else:
            self.name = os.path.expandvars(tree)
            self.is_include_file = False #"FIXME"

class Genparams(dict):
    pass

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
        word = Word(alphanums+':<>.[]_-,=~/')
        conditional = Forward()
        conditional << (Optional("!")("negate") + word("cond") + Suppress('?') + Suppress('(') + OneOrMore(conditional ^ word)("expr") + Suppress(')')).setParseAction(cb_conditional)
        #string = (function ^ word)
        string = word
        string_list = OneOrMore(conditional ^ string)
        s = ' '.join(string_list.parseString(self.__str__()))
        logger.debug("Parsing '{}' with flags {} => {}".format(self.__str__(),
                                                               str(_flags),s))
        return s

class StringOrList(object):
    def __new__(cls, *args, **kwargs):
        if type(args[0]) == list:
            return [String(s) for s in args[0]]
        elif type(args[0]) == str:
            return [String(args[0])]

class Section(object):
    members = {}
    lists   = {}
    dicts   = {}
    def __init__(self, tree):
        for k, v in tree.items():
            if v is None:
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
                    setattr(_d[_name], 'name', _name)
                setattr(self, k, _d)
            else:
                raise KeyError(k + " in section " + self.__class__.__name__)

class Provider(object):
    def __new__(cls, *args, **kwargs):
        provider_name = args[0]['name']
        if provider_name is None:
            raise RuntimeError('Missing "name" in section [provider]')
        return get_provider(provider_name)(args[0],
                                           "FIXME: core_root is used by local providers",
                                           "FIXME: cache_root can be set in fetch call")

class Core:
    def __init__(self, core_file, cache_root='', build_root=''):
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

        if self.provider:
            self.files_root = os.path.join(cache_root,
                                           self.sanitized_name)
            #Ugly hack. Don't like injecting vars
            #How about a setup function or setters?
            self.provider.core_root  = self.core_root
            self.provider.files_root = self.files_root
        else:
            self.files_root = self.core_root

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

        for scripts in self._get_script_names(flags).values():
            for script in scripts:
                for fs in script.filesets:
                    src_files += [f.name for f in self.filesets[fs].files]

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

    def _get_script_names(self, flags):
        target = self._get_target(flags)
        hooks = {}

        if target and target.hooks:
            for hook in ['pre_build', 'post_build', 'pre_run', 'post_run']:
                scripts = getattr(target.hooks, hook)
                if scripts:
                    hooks[hook] = []
                    for script in self._parse_list(flags, scripts):
                        if not script in self.scripts:
                            raise SyntaxError("Script '{}', requested by target '{}', was not found".format(script, target.name))
                        hooks[hook].append(self.scripts[script])

        return hooks

    def get_scripts(self, files_root, flags):
        self._debug("Getting hooks for flags '{}'".format(str(flags)))
        hooks = {}

        for hook, scripts in self._get_script_names(flags).items():
            hooks[hook] = []
            for script in scripts:
                env = script.env
                env['FILES_ROOT'] = files_root
                _script = {'name' : script.name,
                           'cmd'  : [str(x) for x in script.cmd],
                           'env'  : env}
                hooks[hook].append(_script)
                _s = " Matched {} hook {}"
                self._debug(_s.format(hook, str(_script)))
        return hooks

    def get_tool(self, flags):
        self._debug("Getting tool for flags {}".format(str(flags)))
        tool = None
        if flags.get('tool'):
            tool = flags['tool']
        else:
            _flags = flags.copy()
            _flags['is_toplevel'] = True
            target = self._get_target(_flags)
            if target and target.default_tool:
                tool = str(target.default_tool)

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
                        options[member] = str(_member)
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

    def get_generators(self, flags):
        self._debug("Getting generators for flags {}".format(str(flags)))
        generators = {}
        for k,v in self.generators.items():
            generators[k] = v
            generators[k].root = self.files_root
            self._debug(" Found generator " + k)
        return generators

    def get_parameters(self, flags={}):
        self._debug("Getting parameters for flags '{}'".format(str(flags)))
        target = self._get_target(flags)
        parameters = {}

        if target:
            for _param in target.parameters:
                plist = _param.parse(flags).split('=', 1)

                p = plist[0]

                if not p:
                    continue

                if not p in self.parameters:
                    raise SyntaxError("Parameter '{}', requested by target '{}', was not found".format(p, target.name))

                datatype    = self.parameters[p].datatype
                if len(plist) > 1:
                    default = plist[1]
                else:
                    default     = self.parameters[p].default
                description = self.parameters[p].description
                paramtype   = self.parameters[p].paramtype

                if not datatype in ['bool', 'file', 'int', 'str']:
                    _s = "{} : Invalid datatype '{}' for parameter {}"
                    raise SyntaxError(_s.format(self.name, datatype, p))

                if not paramtype in ['cmdlinearg', 'generic', 'plusarg',
                                     'vlogdefine', 'vlogparam']:
                    _s = "{} : Invalid paramtype '{}' for parameter {}"
                    raise SyntaxError(_s.format(self.name, paramtype, p))
                parameters[p] = {
                    'datatype'  : str(self.parameters[p].datatype),
                    'paramtype' : str(self.parameters[p].paramtype),
                }

                if description:
                    parameters[p]['description'] = str(description)

                if default:
                    if datatype == 'bool':
                        if default.lower() ==  'true':
                            parameters[p]['default'] = True
                        elif default.lower() == 'false':
                            parameters[p]['default'] = False
                        else:
                            _s = "{}: Invalid default value '{}' for bool parameter {}"
                            raise SyntaxError(_s.format(self.name, default, p))
                    elif datatype == 'int':
                        if type(default) == int:
                            parameters[p]['default'] = default
                        else:
                            parameters[p]['default'] = int(default,0)
                    else:
                        parameters[p]['default'] = str(default)
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

    def get_ttptttg(self, flags):
        self._debug("Getting ttptttg for flags {}".format(str(flags)))
        target = self._get_target(flags)
        ttptttg = []

        if not target:
            return ttptttg

        _ttptttg = self._parse_list(flags, target.generate)
        if _ttptttg:
            self._debug(" Matched generator instances {}".format(_ttptttg))
        for gen in _ttptttg:
            if not gen in self.generate:
                raise SyntaxError("Generator instance '{}', requested by target '{}', was not found".format(gen, target.name))
            params = self.generate[gen].parameters or {}
            t = {
                'name'      : gen,
                'generator' : str(self.generate[gen].generator),
                'config'    : dict(params),
                'pos'       : str(self.generate[gen].position or 'append'),
            }
            ttptttg.append(t)
        return ttptttg

    def get_work_root(self, flags):
        _flags = flags.copy()
        _flags['is_toplevel'] = True
        target = self._get_target(_flags)
        if target:
            _flags['target'] = target.name
            tool = self.get_tool(_flags)
            if tool:
                return target.name + '-' + tool
            else:
                raise SyntaxError("Failed to determine work root. Could not resolve tool for target " + target.name)
        else:
            raise SyntaxError("Failed to determine work root. Could not resolve target")

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
        for k, v in sorted(_vpi.items()):
            vpi.append({'name'         : k,
                        'src_files'    : [f.name for f in v['src_files']],
                        'include_dirs' : utils.unique_dirs(v['inc_files']),
                        'libs'         : v['libs'],
            })
        return vpi

    def info(self):
        s = """CORE INFO
Name:      {}
Core root: {}

Targets:
{}
"""
        targets = '\n'.join(sorted(self.targets))
        return s.format(str(self.name),
                        str(self.core_root),
                        targets)

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
        if flags.get('is_toplevel') and flags.get('target'):
            target_name = flags.get('target')
        else:
            target_name = "default"

        if target_name in self.targets:
            self._debug(" Matched target {}".format(target_name))
            return self.targets[target_name]
        else:
            self._debug("Matched no target")

    def _get_filesets(self, flags):
        self._debug("Getting filesets for flags '{}'".format(str(flags)))
        target = self._get_target(flags)
        if not target:
            return []
        filesets = []

        for fs in self._parse_list(flags, target.filesets):
            if not fs in self.filesets:
                raise SyntaxError("Fileset '{}', requested by fileset '{}', was not found".format(fs, target.name))
            filesets.append(self.filesets[fs])

        self._debug(" Matched filesets {}".format(target.filesets))
        return filesets

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
  description : Root elements of the CAPI2 structure
  members:
    - name : name
      type : Vlnv
      desc : VLNV identifier for core
    - name : description
      type : String
      desc : Short description of core
    - name : provider
      type : Provider
      desc : Provider of core
    - name : CAPI=2
      type : String
      desc : Technically a header. Must appear as the first line in the core description file
  dicts:
    - name : filesets
      type : Fileset
      desc : File sets
    - name : generate
      type : Generate
      desc : Parametrized generator configurations
    - name : generators
      type : Generators
      desc : Generator provided by this core
    - name : scripts
      type : Script
      desc : Scripts that are used by the hooks
    - name : targets
      type : Target
      desc : Available targets
    - name : parameters
      type : Parameter
      desc : Available parameters
    - name : vpi
      type : Vpi
      desc : Available VPI modules

Fileset:
  description : A fileset represents a group of file with a common purpose. Each file in the fileset is required to have a file type and is allowed to have a logical_name which can be set for the whole fileset or individually for each file. A fileset can also have dependencies on other cores, specified in the depend section
  members:
    - name : file_type
      type : String
      desc : Default file_type for files in fileset
    - name : logical_name
      type : String
      desc : Default logical_name (i.e. library) for files in fileset
  lists:
    - name : files
      type : File
      desc : Files in fileset
    - name : depend
      type : String
      desc : Dependencies of fileset

Generate:
  description : FIXME
  members:
    - name : generator
      type : String
      desc : FIXME
    - name : parameters
      type : Genparams
      desc : FIXME
    - name : position
      type : String
      desc : FIXME

Generators:
  description : FIXME
  members:
    - name : command
      type : String
      desc : FIXME
    - name : interpreter
      type : String
      desc : FIXME
    - name : description
      type : String
      desc : FIXME
    - name : usage
      type : String
      desc : FIXME

Target:
  description : FIXME
  members:
    - name : default_tool
      type : String
      desc : FIXME
    - name : hooks
      type : Hooks
      desc : FIXME
    - name : tools
      type : Tools
      desc : FIXME
    - name : toplevel
      type : StringOrList
      desc : FIXME
  lists:
    - name : filesets
      type : String
      desc : FIXME
    - name : flags
      type : String #FIXME
      desc : FIXME
    - name : generate
      type : String
      desc : FIXME
    - name : parameters
      type : String
      desc : FIXME
    - name : vpi
      type : String
      desc : FIXME

Tools:
  description : The valid subsections of the Tools section and their options are defined by what Edalize backends are available at runtime. The sections listed here are the ones that were available when the documentation was generated.
  members : []
Hooks:
  description : FIXME
  lists:
    - name : pre_build
      type : String
      desc : FIXME
    - name : post_build
      type : String
      desc : FIXME
    - name : pre_run
      type : String
      desc : FIXME
    - name : post_run
      type : String
      desc : FIXME

Parameter:
  description : FIXME
  members:
    - name : datatype
      type : String
      desc : FIXME
    - name : default
      type : String
      desc : FIXME
    - name : description
      type : String
      desc : FIXME
    - name : paramtype
      type : String
      desc : FIXME
    - name : scope
      type : String
      desc : FIXME

Script:
  description : FIXME
  lists:
    - name : cmd
      type : String
      desc : FIXME
    - name : filesets
      type : String
      desc : FIXME
  dicts:
    - name : env
      type : String
      desc : FIXME

Vpi:
  description : FIXME
  lists:
    - name : libs
      type : String
      desc : FIXME
    - name : filesets
      type : String
      desc : FIXME

"""

def _class_doc(items):
    s = items['description']+'\n\n'
    lines = []
    name_len = 10
    type_len = 4
    for item in items.get('members',[]):
        name_len = max(name_len, len(item['name']))
        type_len = max(type_len, len(item['type'])+3)
        lines.append((item['name'], '`'+item['type']+'`_', item['desc']))
    for item in items.get('dicts',[]):
        name_len = max(name_len, len(item['name']))
        type_len = max(type_len, len(item['type'])+11)
        lines.append((item['name'], "Dict of `{}`_".format(item['type']),item['desc']))
    for item in items.get('lists',{}):
        name_len = max(name_len, len(item['name']))
        type_len = max(type_len, len(item['type'])+11)
        lines.append((item['name'], "List of `{}`_".format(item['type']),item['desc']))

    s += '='*name_len+' '+'='*type_len+' '+'='*11+'\n'
    s += 'Field Name'.ljust(name_len+1)+'Type'.ljust(type_len+1)+'Description\n'
    s += '='*name_len+' '+'='*type_len+' '+'='*11+'\n'
    for line in lines:
        s += line[0].ljust(name_len+1)
        s += line[1].ljust(type_len+1)
        s += line[2]
        s += '\n'
    s += '='*name_len+' '+'='*type_len+' '+'='*11+'\n'
    return s

def _generate_classes(j, base_class):
    for cls, _items in j.items():
        class_members = {'__doc__' : _class_doc(_items)}
        if 'members' in _items:
            class_members['members'] = {}
            for key in _items['members']:
                class_members[key['name']] = None
                class_members['members'][key['name']] = key['type']
        if 'lists' in _items:
            class_members['lists'] = {}
            for key in _items['lists']:
                class_members[key['name']] = []
                class_members['lists'][key['name']] = key['type']
        if 'dicts' in _items:
            class_members['dicts'] = {}
            for key in _items['dicts']:
                class_members[key['name']] = {}
                class_members['dicts'][key['name']] = key['type']

        generatedClass = type(cls, (base_class,), class_members)
        globals()[generatedClass.__name__] = generatedClass

capi2_data = yaml.load(description)

for backend in get_edatools():
    backend_name = backend.__name__
    if hasattr(backend, 'get_doc'):
        if backend_name == "Edatool":
            continue
        tool_options = backend.get_doc(0)
    elif hasattr(backend, 'tool_options'):
        _tool_options = getattr(backend, 'tool_options')
        tool_options = {'description' : 'Options for {} backend'.format(backend_name)}
        for group in ['members', 'lists', 'dicts']:
            if group in _tool_options:
                tool_options[group] = []
                for _name, _type in _tool_options[group].items():
                    tool_options[group].append({'name' : _name,
                                                'type' : _type,
                                                'desc' : ''})
    else:
        continue
    capi2_data['Tools']['members'].append({'name' : backend_name.lower(),
                                           'type' : backend_name,
                                           'desc' : backend_name+'-specific options'})
    capi2_data[backend_name] = tool_options

_generate_classes(capi2_data, Section)

def gen_doc():
    c =  capi2_data.copy()
    s = """CAPI2
=====

CAPI2 (Core API version 2) describes the properties of a core as a YAML data structure.

Types
-----

File
~~~~
FIXME

Genparams
~~~~~~~~~
FIXME

Provider
~~~~~~~~
FIXME

String
~~~~~~
FIXME

StringOrList
~~~~~~~~~~~~

Item is allowed to be either a `String`_ or a list of `String`_

Vlnv
~~~~~~
:-separated VLNV (Vendor, Library, Name, Vendor) identifier

Sections
--------

 The first table lists all valid keywords in the document root while the other tables are keywords for subsections of the tree

"""
    def print_class(items):
        s = items['description']+'\n\n'
        lines = []
        name_len = 10
        type_len = 4
        for item in items.get('members',[]):
            name_len = max(name_len, len(item['name']))
            type_len = max(type_len, len(item['type'])+3)
            lines.append((item['name'], '`'+item['type']+'`_', item['desc']))
        for item in items.get('dicts',[]):
            name_len = max(name_len, len(item['name']))
            type_len = max(type_len, len(item['type'])+11)
            lines.append((item['name'], "Dict of `{}`_".format(item['type']),item['desc']))
        for item in items.get('lists',{}):
            name_len = max(name_len, len(item['name']))
            type_len = max(type_len, len(item['type'])+11)
            lines.append((item['name'], "List of `{}`_".format(item['type']),item['desc']))

        s += '='*name_len+' '+'='*type_len+' '+'='*11+'\n'
        s += 'Field Name'.ljust(name_len+1)+'Type'.ljust(type_len+1)+'Description\n'
        s += '='*name_len+' '+'='*type_len+' '+'='*11+'\n'
        for line in lines:
            s += line[0].ljust(name_len+1)
            s += line[1].ljust(type_len+1)
            s += line[2]
            s += '\n'
        s += '='*name_len+' '+'='*type_len+' '+'='*11+'\n'
        return s

    s += _class_doc(c.pop('Root'))
    for k,v in c.items():
        s += "\n{}\n{}\n\n".format(k, '-'*len(k))
        s += _class_doc(v)

    return s
