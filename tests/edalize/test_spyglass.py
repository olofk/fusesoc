import pytest


def test_spyglass_defaults():
    """ Test if the SpyGlass backend picks up the tool defaults """
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir = os.path.join(tests_dir, __name__, 'defaults')
    paramtypes = ['vlogdefine', 'vlogparam']
    name = 'test_spyglass_0'
    tool = 'spyglass'
    tool_options = {}

    (backend, args, work_root) = setup_backend(
        paramtypes, name, tool, tool_options)
    backend.configure(args)

    compare_files(ref_dir, work_root, [
        'Makefile',
        'spyglass-run-design_read.tcl',
        'spyglass-run-lint_lint_rtl.tcl',
        name + '.prj',
    ])

    backend.build()
    compare_files(ref_dir, work_root, [
        'spyglass.cmd',
    ])


def test_spyglass_tooloptions():
    """ Test passing tool options to the Spyglass backend """
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir = os.path.join(tests_dir, __name__, 'tooloptions')
    paramtypes = ['vlogdefine', 'vlogparam']
    name = 'test_spyglass_0'
    tool = 'spyglass'
    tool_options = {
        'methodology': 'GuideWare/latest/block/rtl_somethingelse',
        'goals': ['lint/lint_rtl', 'some/othergoal'],
        'spyglass_options': ['handlememory yes'],
        'rule_parameters': ['handle_static_caselabels yes'],
    }

    (backend, args, work_root) = setup_backend(
        paramtypes, name, tool, tool_options)
    backend.configure(args)

    compare_files(ref_dir, work_root, [
        'Makefile',
        'spyglass-run-design_read.tcl',
        'spyglass-run-lint_lint_rtl.tcl',
        'spyglass-run-some_othergoal.tcl',
        name + '.prj',
    ])

    backend.build()
    compare_files(ref_dir, work_root, [
        'spyglass.cmd',
    ])
