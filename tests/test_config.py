import tempfile
import os.path

from fusesoc.config import Config

from test_common import cores_root, cache_root, library_root

build_root = 'test_build_root'

EXAMPLE_CONFIG = """
[main]
build_root = {build_root}
cache_root = {cache_root}
cores_root = {cores_root}
library_root = {library_root}

[library.test_lib]
location = {library_root}/test_lib
auto-sync = false
sync-uri = https://github.com/fusesoc/fusesoc-cores
"""

def test_config_file():
    tcf = tempfile.TemporaryFile(mode="w+")
    tcf.write(EXAMPLE_CONFIG.format(
            build_root = build_root,
            cache_root = cache_root,
            cores_root = cores_root,
            library_root = library_root
            )
        )
    tcf.seek(0)

    conf = Config(file=tcf)

    assert conf.build_root == build_root

def test_config_path():
    tcf = tempfile.NamedTemporaryFile(mode="w+")
    tcf.write(EXAMPLE_CONFIG.format(
            build_root = build_root,
            cache_root = cache_root,
            cores_root = cores_root,
            library_root = library_root
            )
        )
    tcf.seek(0)

    conf = Config(path=tcf.name)

    assert conf.library_root == library_root

def test_config_failure():
    tcf = tempfile.NamedTemporaryFile(mode="w+")
    tcf.write(EXAMPLE_CONFIG.format(
            build_root = build_root,
            cache_root = cache_root,
            cores_root = "INCORRECT",
            library_root = library_root
            )
        )
    tcf.seek(0)

    conf = Config(path=tcf.name)

    assert not conf.cores_root == cores_root

def test_config_libraries():
    tcf = tempfile.NamedTemporaryFile(mode="w+")
    tcf.write(EXAMPLE_CONFIG.format(
            build_root = build_root,
            cache_root = cache_root,
            cores_root = cores_root,
            library_root = library_root
            )
        )
    tcf.seek(0)

    conf = Config(path=tcf.name)

    assert conf.libraries['test_lib']['location'] == os.path.join(library_root, 'test_lib')
    assert conf.libraries['test_lib']['sync-uri'] == 'https://github.com/fusesoc/fusesoc-cores'
    assert not conf.libraries['test_lib']['auto-sync']

