from orpsoc.provider import Provider
import os.path
import pysvn

class ProviderOpenCores(Provider):
    def __init__(self, config):
        self.repo_path = 'http://opencores.org/ocsvn/' + \
            config.get('repo_name') + '/' + config.get('repo_name') + '/' + \
            config.get('repo_root')
        self.revision_number  = config.get('revision')
        self.revision = pysvn.Revision(pysvn.opt_revision_kind.number, self.revision_number)
        self.client = pysvn.Client()

    def fetch(self, local_dir):

        status = self.status(local_dir)

        if status == 'empty':
            self._checkout(local_dir)
        elif status == 'modified':
            self.clean_cache()
            self._checkout(local_dir)
        elif status == 'outofdate':
            self._update()
        elif status == 'downloaded':
            pass
        else:
            print("provider status is: " + status + " This shouldn't happen")

    def status(self, local_dir):
        #FIXME: Check if repo is modified, or is an SVN repo at all, etc..
        if not os.path.isdir(local_dir):
            return 'empty'
        else:
            return 'downloaded'
        
    def _checkout(self, local_dir):
        print("Checking out " + self.repo_path + " revision " + self.revision_number + " to " + local_dir)
        try:
            self.client.checkout(self.repo_path,
                            local_dir,
                            revision=self.revision)
        except pysvn.ClientError:
            print("Error: Failed to checkout " + self.repo_path)
            exit(1)

    def _update(self):
        self.client.update(local_dir, self.revision)
