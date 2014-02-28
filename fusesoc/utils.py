import subprocess

class Launcher:
    def __init__(self, cmd, args=[], shell=False, cwd=None, stderr_path=None, errormsg=None, env=None):
        self.cmd      = cmd
        self.args     = args
        self.shell    = shell
        self.cwd      = cwd
        self.errormsg = errormsg
        self.env      = env
        self.stderr_path = stderr_path
        self.stderr = None
        if stderr_path != None:
            self.stderr = open(self.stderr_path, 'w')	

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
            if self.stderr_path is None:
                self.stderr_path = "stderr"
            if self.errormsg is None:
                self.errormsg = '"' + str(self) + '" exited with an error code. See ' + self.stderr_path + ' for details'
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
        
