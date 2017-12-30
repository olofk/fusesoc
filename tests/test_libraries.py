import tempfile
import shutil
import os.path
import logging
import subprocess

from argparse import Namespace

from fusesoc.config import Config

from test_common import cores_root, build_root, cache_root, library_root

EXAMPLE_CONFIG = """
[main]
build_root = {build_root}
cache_root = {cache_root}
library_root = {library_root}

[library.test_lib]
location = {cores_root}
auto-sync = {auto_sync}
sync-uri = {sync_uri}
"""

sync_uri = 'https://github.com/fusesoc/fusesoc-cores'

def _run_test_util(cm, args):
    from fusesoc.main import _get_core
    _get_core(cm, 'mor1kx-generic')
    _get_core(cm, 'atlys')

def test_library_location():
    from fusesoc.main import run

    tcf = tempfile.TemporaryFile(mode="w+")
    tcf.write(EXAMPLE_CONFIG.format(
            build_root = build_root,
            cache_root = cache_root,
            cores_root = cores_root,
            library_root = library_root,
            auto_sync = 'false',
            sync_uri = sync_uri
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

def test_library_update(caplog):
    from fusesoc.main import update, run

    clone_target = tempfile.mkdtemp()

    try:
        subprocess.call(['git', 'clone', sync_uri, clone_target])

        tcf = tempfile.TemporaryFile(mode="w+")
        tcf.write(EXAMPLE_CONFIG.format(
                build_root = build_root,
                cache_root = cache_root,
                cores_root = clone_target,
                library_root = library_root,
                auto_sync = 'false',
                sync_uri = sync_uri
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
        args.libraries = []
        args.func = update

        with caplog.at_level(logging.INFO):
            run(args)

        assert not "Updating 'test_lib'" in caplog.text

        caplog.clear()

        args.libraries = ['test_lib']

        with caplog.at_level(logging.INFO):
            run(args)

        assert "Updating 'test_lib'" in caplog.text

        caplog.clear()

        args.libraries = []
        conf.libraries['test_lib']['auto-sync'] = True

        with caplog.at_level(logging.INFO):
            run(args)

        assert "Updating 'test_lib'" in caplog.text

        caplog.clear()

    finally:
        shutil.rmtree(clone_target)
