import subprocess

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
            raise RuntimeError("Error: Command " + self.cmd + " not found. Make sure it is in $PATH")
        except subprocess.CalledProcessError:
            if self.stderr is None:
                output = "stderr"
            else:
                output = self.stderr.name
            if self.errormsg is None:
                self.errormsg = '"' + str(self) + '" exited with an error code. See ' + output + ' for details'
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
        
def launch(cmd, args=[], shell=False, cwd=None, stderr=None):
    try:
        subprocess.check_call([cmd] + args,
                              cwd = cwd,
                              shell = shell,
                              stderr = stderr),
    except OSError:
        print("Error: Command " + cmd + " not found. Make sure it is in $PATH")
        exit(1)
    except subprocess.CalledProcessError:
        if stderr is None:
            stderr = "stderr"
        print("Error: " + cmd + ' '.join(args) + " returned errors. See " + stderr + " for details")
        exit(1)
