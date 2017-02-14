import subprocess
import re
import sys
from fusesoc.config import Config

if sys.version[0] == '2':
    FileNotFoundError = OSError

from fusesoc.config import Config

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
        if Config().verbose:
            pr_info(self.cwd)
            pr_info('    ' + str(self))
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
                if Config().verbose:
                    with open(self.stderr.name, 'r') as f:
                        pr_err(f.read())

            if self.errormsg is None:
                self.errormsg = '"' + str(self) + '" exited with an error code.\nERROR: See ' + output + ' for details.'
            raise RuntimeError(self.errormsg)

    def __str__(self):
        return ' '.join([self.cmd] + self.args)


def convert_V2H( read_file, write_file):
            fV = open (read_file,'r')
            fC = open (write_file,'w')
            fC.write("//File auto-converted the Verilog to C. converted by FuseSoC//\n")
            fC.write("//source file --> " + read_file + "\n")
            for line in fV:
                Sline=line.split('`',1)
                if len(Sline) == 1:
                    fC.write(Sline[0])
                else:
                    fC.write(Sline[0]+"#"+Sline[1])
            fC.close
            fV.close

def run_scripts(scripts, scripts_root, cwd, env):
    for script_name in scripts:
        script = os.path.abspath(os.path.join(scripts_root, script_name))
        pr_info("Running " + script);
        Launcher(script, cwd = cwd, env = env, shell=True).run()
    
def find_verilator():
    verilator_root = os.getenv('VERILATOR_ROOT')
    if verilator_root is None:
        output = which('verilator')
        if not output:
            return None
        return output[0]

    return os.path.join(verilator_root,'bin','verilator')

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

def pr_err(msg):
    if Config().monochrome:
        print('ERROR: ' + msg)
    else:
        print('\033[1;31m' + 'ERROR: ' + msg + '\033[0m')


def pr_warn(msg):
    if Config().monochrome:
        print('WARN:  ' + msg)
    else:
        print('\033[1;33m' + 'WARN:  ' + msg + '\033[0m')

def pr_info(msg):
    if Config().monochrome:
        print('INFO:  ' + msg)
    else:
        print('\033[1;37m' + 'INFO:  ' + msg + '\033[0m')

def unique_dirs(file_list):
    return list(set([os.path.dirname(f.name) for f in file_list]))
