"""
Test different use-cases in terms of user-supplied command line invocations.

This module contains tests, that test some kind of end-to-end-behavior, i.e. a
set of fusesoc-commands grouped together, because they form a use-case. This
module has a special fixture called `run_in_temporary_directory`, which is used
by all tests (in this module) and causes that test to be executed inside a
temporary directory automatically deleted on exit of the test. Note, that each
test is run in a different directory.

The testcases can leverage the `_fusesoc()`-function to invoke the `fusesoc`
command with its parameters, just as it would be called on the commandline, e.g.
`fusesoc library update` would be executed via `_fusesoc("library", "update")`.
"""

import os
import sys
import tempfile
from unittest.mock import patch

import pytest

from fusesoc.main import main


def test_git_library_with_default_branch_is_added_and_updated(caplog):
    _fusesoc("library", "add", "https://github.com/fusesoc/fusesoc-generators")
    assert "Cloning library into fusesoc_libraries/fusesoc-generators" in caplog.text

    caplog.clear()
    _fusesoc("library", "update")
    assert "Updating..." in caplog.text


def test_update_git_library_with_fixed_version(caplog, capsys):
    """
    Previously, one could not successfully use `fusesoc library update` on
    libraries with specific sync versions. This test checks, that no error is
    reported in that case.
    """
    url = "https://github.com/fusesoc/fusesoc-generators"
    _fusesoc("library", "add", url, "--sync-version", "v0.1.4")
    assert "Checked out fusesoc-generators at version v0.1.4" in caplog.text

    _fusesoc("library", "list")
    output = capsys.readouterr().out
    assert "fusesoc-generators" in output
    assert "v0.1.4" in output

    _fusesoc("library", "update")
    assert "Failed to update library" not in caplog.text

    _fusesoc("library", "list")
    output = capsys.readouterr().out
    assert "fusesoc-generators" in output
    assert "v0.1.4" in output


def test_usage_error_leads_to_nonzero_exit_code():
    with pytest.raises(SystemExit):
        _fusesoc("--option_does_not_exist")


def test_failing_generator_is_not_cached(caplog, capfd):
    """
    When FuseSoC runs generators, the output is cached if the generator requests
    so. While this is generally a good idea, the cached output must not be used
    in subsequent runs if the generator fails with a non-zero exit code. In that
    case, the generator should be re-invoked in the next run to not need to user
    to manually run `fusesoc gen clean` to fix a faulty cache entry.

    Therefore this tests adds a simple generator, which prints something to the
    console and then exist with an error. After registering this generator, two
    FuseSoC-runs are performed, where the generator, despited being marked as
    cacheable, needs to be reinvoked.
    """
    # Register the generator
    with open("failing-script.py", "w") as command:
        command.write("import sys; print('Running generator'); sys.exit(2)")
    with open("test-generator.core", "w") as failing_generator:
        failing_generator.write(
            """\
CAPI=2:
name: ::test-generator:0.1.0
generators:
  failing-generator:
    # Run a builtin POSIX command, which prints something and then exits with a
    # non-zero exit code. `printf` can be used with formatting something that is
    # not an integer as one, causing it to fail.
    interpreter: python
    command: failing-script.py
    cache_type: input
            """
        )
    _fusesoc("library", "add", ".")
    _fusesoc("gen", "clean")
    _fusesoc("gen", "list")
    captured = capfd.readouterr()
    assert "::test-generator:0.1.0" in captured.out

    with open("test-user.core", "w") as using_core:
        using_core.write(
            """\
CAPI=2:
name: ::test-user:0.1.0
filesets:
  rtl:
    depend: ["::test-generator:0.1.0"]
generate:
  call-generator:
    generator: failing-generator
targets:
  default:
    filesets: [rtl]
    generate: [call-generator]
            """
        )

    # run generator the first time, which should fail
    with pytest.raises(SystemExit):
        _fusesoc("run", "--tool=icarus", "::test-user:0.1.0")
    captured = capfd.readouterr()
    assert "Found cached output for ::test-user-call-generator:0.1.0" not in caplog.text
    assert captured.out == "Running generator\n"

    # run generator second time, which should fail as well despite being cached
    with pytest.raises(SystemExit):
        _fusesoc("run", "--tool=icarus", "::test-user:0.1.0")
    captured = capfd.readouterr()
    assert "Found cached output for ::test-user-call-generator:0.1.0" not in caplog.text
    assert captured.out == "Running generator\n"


# region Test fixtures and helper functions
@pytest.fixture(autouse=True)  # this fixture will be used by all tests implicitly
def run_in_temporary_directory(request):
    """Create temporary directory to run each test in (deleted automatically)"""
    with tempfile.TemporaryDirectory(prefix=request.function.__name__) as directory:
        os.chdir(directory)
        os.environ["XDG_CONFIG_HOME"] = os.path.join(directory, ".config")
        os.environ["XDG_CACHE_HOME"] = os.path.join(directory, ".cache")
        os.environ["XDG_DATA_HOME"] = os.path.join(directory, ".local", "share")
        yield directory
        os.chdir(request.config.invocation_params.dir)


def _fusesoc(*args: str) -> None:
    """
    Execute the `fusesoc` CLI-command with the given command line arguments.

    This function will execute the `main()`-function of this tool with the
    user-supplied set of command line arguments. This allows for ergonomic test
    creation, since one can (more or less) write the command one would type into
    the terminal within tests. This is great for end-to-end/use-case tests.

    A non-zero exit code of the application will be propagated via an exception.
    """
    args = ["fusesoc"] + [*args]
    with patch.object(sys, "argv", args):
        main()


# endregion
