import logging
import shutil
from fusesoc.provider.provider import Provider
from fusesoc.utils import Launcher

logger = logging.getLogger(__name__)

class Git(Provider):

    def _checkout(self, local_dir):
        if 'version' in self.config:
            version = self.config.get('version')
        else:
            version = None

        #TODO : Sanitize URL
        repo   = self.config.get('repo')
        logger.info("Checking out " + repo + " to " + local_dir)
        args = ['clone', '-q', repo, local_dir]
        Launcher('git', args).run()
        if version:
            args = ['-C', local_dir, 'checkout', '-q', version]
            Launcher('git', args).run()

PROVIDER_CLASS = Git
