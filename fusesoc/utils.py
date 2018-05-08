import subprocess
import logging
import sys
import importlib

if sys.version[0] == '2':
    FileNotFoundError = OSError

logger = logging.getLogger(__name__)

class Launcher:
    def __init__(self, cmd, args=[], shell=False, cwd=None, stderr=None, stdout=None, errormsg=None, env=None):
        self.cmd      = cmd
        self.args     = args
        self.shell    = shell
        self.cwd      = cwd
        self.stderr   = stderr
        self.stdout   = stdout
        self.errormsg = errormsg
        self.env      = env

    def run(self):
        logger.debug(self.cwd)
        logger.debug('    ' + str(self))
        try:
            subprocess.check_call([self.cmd] + self.args,
                                  cwd = self.cwd,
                                  env = self.env,
                                  shell = self.shell,
                                  stderr = self.stderr,
                                  stdout = self.stdout,
                                  stdin=subprocess.PIPE),
        except FileNotFoundError:
            raise RuntimeError("Command '" + self.cmd + "' not found. Make sure it is in $PATH")
        except subprocess.CalledProcessError:
            if self.stderr is None:
                output = "stderr"
            else:
                output = self.stderr.name
                with open(self.stderr.name, 'r') as f:
                    logger.error(f.read())

            if self.errormsg is None:
                self.errormsg = '"' + str(self) + '" exited with an error code.\nERROR: See ' + output + ' for details.'
            raise RuntimeError(self.errormsg)

    def __str__(self):
        return ' '.join([self.cmd] + self.args)

def is_mingw():
    if sys.platform == "msys":
        return True
    return (sys.platform == "win32" and "GCC" in sys.version)

def cygpath(win_path):
    path = subprocess.check_output(["cygpath", "-u", win_path])
    return path.decode('ascii').strip()

import os

def unique_dirs(file_list):
    return list(set([os.path.dirname(f.name) for f in file_list]))


# With help from:
# http://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
# Very minimal direct copying so should be no license issues.

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# These are the sequences need to get colored output.
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"

COLOR_MAP = {
    'CRITICAL': RED,
    'ERROR': RED,
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': WHITE,
    }


class ColoredFormatter(logging.Formatter):

    def __init__(self, msg, monochrome):
        super(ColoredFormatter, self).__init__(msg)
        self.monochrome = monochrome

    def format(self, record):
        uncolored = super(ColoredFormatter, self).format(record)
        levelname = record.levelname
        if not self.monochrome and (levelname in COLOR_MAP):
            color_seq = COLOR_SEQ % (30 + COLOR_MAP[levelname])
            formatted = color_seq + uncolored + RESET_SEQ
        else:
            formatted = uncolored
        return formatted


def setup_logging(level, monchrome=False, log_file=None):
    '''
    Utility function for setting up logging.
    '''
    # Logging to file
    if log_file:
        logging.basicConfig(filename=log_file, filemode='w',
                            level=logging.DEBUG)

    # Pretty color terminal logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = ColoredFormatter("%(levelname)s: %(message)s", monchrome)
    ch.setFormatter(formatter)
    # Which packages do we want to log from.
    packages = ('__main__', 'fusesoc',)
    for package in packages:
        logger = logging.getLogger(package)
        logger.addHandler(ch)
        logger.setLevel(level)
    # Warning only packages
    warning_only_packages = []
    for package in warning_only_packages:
        logger = logging.getLogger(package)
        logger.addHandler(ch)
        logger.setLevel(logging.WARNING)
    logger.debug('Setup logging at level {}.'.format(level))
