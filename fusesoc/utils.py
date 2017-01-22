import subprocess
import logging
import sys
from fusesoc.config import Config

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

def cygpath(win_path):
    path = subprocess.check_output(["cygpath", "-u", win_path])
    return path.decode('ascii').strip()

#Copied from http://twistedmatrix.com/trac/browser/tags/releases/twisted-8.2.0/twisted/python/procutils.py

#Permission is hereby granted, free of charge, to any person obtaining
#a copy of this software and associated documentation files (the
#"Software"), to deal in the Software without restriction, including
#without limitation the rights to use, copy, modify, merge, publish,
#distribute, sublicense, and/or sell copies of the Software, and to
#permit persons to whom the Software is furnished to do so, subject to
#the following conditions:
#
#The above copyright notice and this permission notice shall be
#included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
#LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
#OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
#WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import os

def which(name, flags=os.X_OK):
    """Search PATH for executable files with the given name.

    On newer versions of MS-Windows, the PATHEXT environment variable will be
    set to the list of file extensions for files considered executable. This
    will normally include things like ".EXE". This fuction will also find files
    with the given name ending with any of these extensions.

    On MS-Windows the only flag that has any meaning is os.F_OK. Any other
    flags will be ignored.

    @type name: C{str}
    @param name: The name for which to search.

    @type flags: C{int}
    @param flags: Arguments to L{os.access}.

    @rtype: C{list}
    @param: A list of the full paths to files found, in the
    order in which they were found.
    """
    result = []
    exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
    path = os.environ.get('PATH', None)
    if path is None:
        return []
    for p in os.environ.get('PATH', '').split(os.pathsep):
        p = os.path.join(p, name)
        if os.access(p, flags):
            result.append(p)
        for e in exts:
            pext = p + e
            if os.access(pext, flags):
                result.append(pext)
    return result

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


def setup_logging(level, monchrome=False):
    '''
    Utility function for setting up logging.
    '''
    # Logging to file
    logging.basicConfig(filename='fusesoc.log', filemode='w', level=logging.DEBUG)
    # Pretty color terminal logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = ColoredFormatter("%(levelname)s: %(message)s", monochrome=monchrome)
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
