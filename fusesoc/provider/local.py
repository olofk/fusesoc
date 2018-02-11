import logging
import os.path
from fusesoc.provider.provider import Provider

logger = logging.getLogger(__name__)

class Local(Provider):
    @staticmethod
    def init_library(library):
        if not os.path.isdir(library['location']):
            logger.error("Local library at location '{}' not found.".format(library['location']))
            exit(1)

    def _checkout(self, local_dir):
        pass

    @staticmethod
    def update_library(library):
        pass
