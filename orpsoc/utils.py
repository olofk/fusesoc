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
                self.stderr = "stderr"
                if self.errormsg:
                    raise RuntimeError(self.errormsg)
                else:
                    raise RuntimeError("Error: " + self.cmd + ' '.join(self.args) + " returned errors. See " + self.stderr + " for details")

    def __str__(self):
        return self.cmd + ' ' + ' '.join(self.args)
        
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
