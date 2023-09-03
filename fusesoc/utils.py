# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import subprocess
import sys
import warnings

import yaml

try:
    from yaml import CSafeDumper as YamlDumper
    from yaml import CSafeLoader as YamlLoader
except ImportError:
    from yaml import SafeDumper as YamlDumper
    from yaml import SafeLoader as YamlLoader

from fusesoc.capi2.inheritance import Inheritance

logger = logging.getLogger(__name__)


class Launcher:
    def __init__(self, cmd, args=[], cwd=None):
        self.cmd = cmd
        self.args = args
        self.cwd = cwd

    def run(self):
        """Runs the cmd with args after converting them all to strings via str"""
        logger.debug(self.cwd or "./")
        logger.debug("    " + str(self))
        try:
            subprocess.check_call(
                map(str, [self.cmd] + self.args),
                cwd=self.cwd,
            ),
        except FileNotFoundError:
            raise RuntimeError(
                "Command '" + self.cmd + "' not found. Make sure it is in $PATH"
            )
        except subprocess.CalledProcessError:
            self.errormsg = '"{}" exited with an error code. See stderr for details.'
            raise RuntimeError(self.errormsg.format(str(self)))

    def __str__(self):
        return " ".join(map(str, [self.cmd] + self.args))


def is_mingw():
    if sys.platform == "msys":
        return True
    return sys.platform == "win32" and "GCC" in sys.version


def cygpath(win_path):
    path = subprocess.check_output(["cygpath", "-u", win_path])
    return path.decode("ascii").strip()


import os


def unique_dirs(file_list):
    return list({os.path.dirname(f) for f in file_list})


# With help from:
# http://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
# Very minimal direct copying so should be no license issues.

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# These are the sequences need to get colored output.
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"

COLOR_MAP = {
    "CRITICAL": RED,
    "ERROR": RED,
    "WARNING": YELLOW,
    "INFO": WHITE,
    "DEBUG": WHITE,
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, monochrome):
        super().__init__(msg)
        self.monochrome = monochrome

    def format(self, record):
        uncolored = super().format(record)
        levelname = record.levelname
        if not self.monochrome and (levelname in COLOR_MAP):
            color_seq = COLOR_SEQ % (30 + COLOR_MAP[levelname])
            formatted = color_seq + uncolored + RESET_SEQ
        else:
            formatted = uncolored
        return formatted


def setup_logging(level, monchrome=False, log_file=None):
    """
    Utility function for setting up logging.
    """
    # Logging to file
    if log_file:
        logging.basicConfig(filename=log_file, filemode="w", level=logging.DEBUG)

    # Redirect Python warnings (from the warnings module) to the standard
    # logging infrastructure. Warnings end up in the py.warnings category.
    logging.captureWarnings(True)

    def _formatwarning(message, category, filename, lineno, line=None):
        # Format FutureWarnings, which are intended for end users, in a way
        # that strips out all code references, which are meaningless to an end
        # user.
        if category == FutureWarning:
            return message

        return _formatwarning_orig(message, category, filename, lineno, line)

    _formatwarning_orig = warnings.formatwarning
    warnings.formatwarning = _formatwarning

    # Pretty color terminal logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = ColoredFormatter("%(levelname)s: %(message)s", monchrome)
    ch.setFormatter(formatter)
    # Which packages do we want to log from.
    packages = (
        "__main__",
        "fusesoc",
        "edalize",
        "py.warnings",
    )
    for package in packages:
        package_logger = logging.getLogger(package)
        package_logger.addHandler(ch)
        package_logger.setLevel(level)
    # Warning only packages
    warning_only_packages = []
    for package in warning_only_packages:
        package_logger = logging.getLogger(package)
        package_logger.addHandler(ch)
        package_logger.setLevel(logging.WARNING)
    logger.debug(f"Setup logging at level {level}.")


def yaml_fwrite(filepath, content, preamble=""):
    with open(filepath, "w") as f:
        if len(preamble) > 0:
            f.write(preamble + "\n")
        f.write(yaml.dump(content, Dumper=YamlDumper, sort_keys=False))


def yaml_fread(filepath, resolve_env_vars=False, remove_preamble=False):
    with open(filepath) as f:
        if remove_preamble:
            f.readline()
        return yaml_read(f.read(), resolve_env_vars)


def yaml_read(data, resolve_env_vars=False):
    try:
        data = Inheritance.yaml_merge_2_fusesoc_merge(data)
        capi_data = {}
        if resolve_env_vars:
            capi_data = yaml.load(os.path.expandvars(data), Loader=YamlLoader)
        else:
            capi_data = yaml.load(data, Loader=YamlLoader)
        return Inheritance.elaborate_inheritance(capi_data)
    except (yaml.parser.ParserError, yaml.scanner.ScannerError) as e:
        raise SyntaxError(str(e))


def yaml_dump(data):
    return yaml.dump(data)


def merge_dict(d1, d2, concat_list_appends_only=False):
    for key, value in d2.items():
        if isinstance(value, dict):
            d1[key] = merge_dict(d1.get(key, {}), value)
        elif isinstance(value, list) and (
            not concat_list_appends_only or key.endswith("_append")
        ):
            d1[key] = d1.get(key, []) + value
        else:
            d1[key] = value
    return d1
