import tempfile
import os.path

from argparse import Namespace

from fusesoc.config import Config
from fusesoc.main import run

from test_common import cores_root, build_root, cache_root, library_root

EXAMPLE_CONFIG = """
[main]
build_root = {build_root}
cache_root = {cache_root}
library_root = {library_root}

[library.test_lib]
location = {cores_root}
auto-sync = false
sync-uri = https://github.com/fusesoc/fusesoc-cores
"""

def _run_test_util(cm, args):
    from fusesoc.main import _get_core
    _get_core(cm, 'mor1kx-generic')
    _get_core(cm, 'atlys')

def test_library_location():
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
    
    args = Namespace()
    
    # TODO find a better way to set up these defaults
    args.verbose = False
    args.monochrome = False
    args.cores_root = []
    vars(args)['32'] = False
    vars(args)['64'] = False
    
    args.config = tcf
    args.func = _run_test_util
    
    run(args)
