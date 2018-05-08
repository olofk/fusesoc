from collections import OrderedDict
import logging

import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

import os
import importlib

logger = logging.getLogger(__name__)

class Config(object):

    def __init__(self, path=None, file=None):
        self.build_root = None
        self.cache_root = None
        self.cores_root = []
        self.systems_root = None
        self.library_root = None
        self.libraries = OrderedDict()

        config = configparser.SafeConfigParser()
        if file is None:
            if path is None:
                xdg_config_home = os.environ.get('XDG_CONFIG_HOME') or \
                          os.path.join(os.path.expanduser('~'), '.config')
                config_files = ['/etc/fusesoc/fusesoc.conf',
                        os.path.join(xdg_config_home, 'fusesoc','fusesoc.conf'),
                        'fusesoc.conf']
            else:
                logger.debug("Using config file '{}'".format(path))
                if not os.path.isfile(path):
                    with open(path, 'a'):
                        pass
                config_files = [path]

            logger.debug('Looking for config files from ' + ':'.join(config_files))
            files_read = config.read(config_files)
            logger.debug('Found config files in ' + ':'.join(files_read))
            if files_read:
                self._path = files_read[-1]
        else:
            logger.debug('Using supplied config file')
            if sys.version[0] == '2':
                config.readfp(file)
            else:
                config.read_file(file)
            file.seek(0)
            self._path = file.name

        for item in ['build_root', 'cache_root', 'systems_root', 'library_root']:
            try:
                setattr(self, item, os.path.expanduser(config.get('main', item)))
            except configparser.NoOptionError:
                pass
            except configparser.NoSectionError:
                pass
        item = 'cores_root'
        try:
            setattr(self, item, config.get('main', item).split())
        except configparser.NoOptionError:
            pass
        except configparser.NoSectionError:
            pass

        #Set fallback values
        if self.build_root is None:
            self.build_root   = os.path.abspath('build')
        if self.cache_root is None:
            xdg_cache_home = os.environ.get('XDG_CACHE_HOME') or \
                             os.path.join(os.path.expanduser('~'), '.cache')
            self.cache_root = os.path.join(xdg_cache_home, 'fusesoc')
            if not os.path.exists(self.cache_root):
                os.makedirs(self.cache_root)
        if not self.cores_root and os.path.exists('cores'):
            self.cores_root   = [os.path.abspath('cores')]
        if self.systems_root is None and os.path.exists('systems'):
            self.systems_root = os.path.abspath('systems')
        if self.library_root is None:
            xdg_data_home = os.environ.get('XDG_DATA_HOME') or \
                             os.path.join(os.path.expanduser('~'), '.local/share')
            self.library_root = os.path.join(xdg_data_home, 'fusesoc')

        # Parse library sections
        library_sections = [x for x in config.sections() if x.startswith('library')]
        for section in library_sections:
            library = section.partition('.')[2]
            try:
                location = config.get(section, 'location')
            except configparser.NoOptionError:
                location = os.path.join(self.library_root, library)

            try:
                auto_sync = config.getboolean(section, 'auto-sync')
            except configparser.NoOptionError:
                auto_sync = True
            except ValueError as e:
                _s = "Error parsing auto-sync '{}'. Ignoring library '{}'"
                logger.warn(_s.format(str(e), library))
                continue

            try:
                sync_uri = config.get(section, 'sync-uri')
            except configparser.NoOptionError:
                # sync-uri is absent for local libraries
                sync_uri = None

            try:
                sync_type = config.get(section, 'sync-type')
            except configparser.NoOptionError:
                # sync-uri is absent for local libraries
                sync_type = None

            self.libraries[library] = {
                    'location': location,
                    'auto-sync': auto_sync,
                    'sync-uri': sync_uri,
                    'sync-type': sync_type
                }

        logger.debug('build_root='+self.build_root)
        logger.debug('cache_root='+self.cache_root)
        logger.debug('cores_root='+':'.join(self.cores_root))
        logger.debug('systems_root='+self.systems_root if self.systems_root else "Not defined")
        logger.debug('library_root='+self.library_root)

    def add_library(self, name, library):
        from fusesoc.provider import get_provider
        if not hasattr(self, '_path'):
            raise RuntimeError("No FuseSoC config file found - can't add library")
        section_name = 'library.' + name

        config = configparser.SafeConfigParser()
        config.read(self._path)

        if not section_name in config.sections():
            config.add_section(section_name)

        # This is not user-controlled at all so an assert is OK
        assert('location' in library or 'sync-uri' in library);

        # sync-uri is absent for local libraries
        if 'sync-uri' in library:
            config.set(section_name, 'sync-uri', library['sync-uri'])

        if 'sync-type' in library:
            config.set(section_name, 'sync-type', library['sync-type'])
        else:
            library['sync-type'] = 'git'

        if 'auto-sync' in library:
            if library['auto-sync']:
                config.set(section_name, 'auto-sync', 'true')
            else:
                config.set(section_name, 'auto-sync', 'false')
        else:
            library['auto-sync'] = True

        if 'location' in library:
            config.set(section_name, 'location', library['location'])
        else:
            library['location'] = os.path.join(self.library_root, name)

        self.libraries[name] = library

        try:
            provider = get_provider(library['sync-type'])
        except ImportError as e:
            raise RuntimeError("Invalid sync-type '{}'".format(library['sync-type']))

        provider.init_library(library)

        with open(self._path, 'w') as conf_file:
            config.write(conf_file)
