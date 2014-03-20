import subprocess
import re

class Launcher:
    def __init__(self, cmd, args=[], shell=False, cwd=None, stderr=None, errormsg=None, env=None):
        self.cmd      = cmd
        self.args     = args
        self.shell    = shell
        self.cwd      = cwd
        self.stderr   = stderr
        self.errormsg = errormsg
        self.env      = env

    def run(self):
        try:
            subprocess.check_call([self.cmd] + self.args,
                                  cwd = self.cwd,
                                  env = self.env,
                                  shell = self.shell,
                                  stderr = self.stderr,
                                  stdin=subprocess.PIPE),
        except OSError:
            raise RuntimeError("Command " + self.cmd + " not found. Make sure it is in $PATH")
        except subprocess.CalledProcessError:
            if self.stderr is None:
                output = "stderr"
            else:
                output = self.stderr.name
            if self.errormsg is None:
                self.errormsg = '"' + str(self) + '" exited with an error code.\n\nSee ' + output + ' for details.'
            raise RuntimeError(self.errormsg)

    def __str__(self):
        return self.cmd + ' ' + ' '.join(self.args)


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

def find_verilator():
    verilator_root = os.getenv('VERILATOR_ROOT')
    if verilator_root is None:
        output = which('verilator')
        if not output:
            return None
        return output[0]

    return os.path.join(verilator_root,'bin','verilator')

def get_verilator_root():
    verilator_root = os.getenv('VERILATOR_ROOT')
    if verilator_root is not None:
        return verilator_root;

    # VERILATOR_ROOT not set, run 'verilator -V' and 'grep' the hardcoded
    # value out of the output.
    verilator = find_verilator()
    if verilator is None:
        return None
    output = subprocess.check_output(verilator + ' -V',
                                     shell=True).splitlines();
    pattern = re.compile("VERILATOR_ROOT")
    for l in output:
        if pattern.search(l):
            return l.split('=')[1].strip()

    return None


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
    print('\033[1;31m' + 'ERROR: ' + msg + '\033[0m')

def pr_warn(msg):
    print('\033[1;33m' + 'WARN:  ' + msg + '\033[0m')

def pr_info(msg):
    print('\033[1;37m' + 'INFO:  ' + msg + '\033[0m')
