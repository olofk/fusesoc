import subprocess

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
