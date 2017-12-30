import tempfile

from fusesoc.config import Config

from test_common import cores_root, build_root, cache_root

EXAMPLE_CONFIG = """
[main]
build_root = {build_root}
cache_root = {cache_root}
cores_root = {cores_root}
"""

def test_config_file():
    tcf = tempfile.TemporaryFile(mode="w+")
    tcf.write(EXAMPLE_CONFIG.format(
            build_root = build_root,
            cache_root = cache_root,
            cores_root = cores_root
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
            cores_root = cores_root
            )
        )
    tcf.seek(0)
    
    conf = Config(path=tcf.name)
    
    assert conf.cache_root == cache_root

def test_config_failure():
    tcf = tempfile.NamedTemporaryFile(mode="w+")
    tcf.write(EXAMPLE_CONFIG.format(
            build_root = build_root,
            cache_root = cache_root,
            cores_root = "INCORRECT"
            )
        )
    tcf.seek(0)
    
    conf = Config(path=tcf.name)
    
    assert not conf.cores_root == cores_root

