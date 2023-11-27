import logging
import os
import subprocess

from yaml import dump, load

try:
    from yaml import CDumper as Dumper
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Dumper, Loader

logger = logging.getLogger(__name__)


class Custom:
    def run(self, edam, work_root):
        fin = "custom_filter_input.yml"
        fout = "custom_filter_output.yml"
        cmd = os.environ.get("FUSESOC_CUSTOM_FILTER")
        if not cmd:
            logger.error("Environment variable FUSESOC_CUSTOM_FILTER was not set")
            return
        with open(os.path.join(work_root, fin), "w") as f:
            dump(edam, f, Dumper=Dumper)

        subprocess.run([cmd, fin, fout], cwd=work_root)
        with open(os.path.join(work_root, fout)) as f:
            edam = load(f, Loader=Loader)

        return edam
