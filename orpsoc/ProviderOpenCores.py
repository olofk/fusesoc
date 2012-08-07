import os.path
import pysvn

class ProviderOpenCores: #(Provider):
    def __init__(self, config):
        self.repo_path = 'http://opencores.org/ocsvn/' + \
            config.get('repo_name') + '/' + config.get('repo_name') + '/' + \
            config.get('repo_root')
        self.revision  = config.get('revision')

    def fetch(self, local_dir):
        revision = pysvn.Revision(pysvn.opt_revision_kind.number, self.revision)
        client = pysvn.Client()
        if os.path.isdir(local_dir):
            print("Repo already checked out")
               #FIXME: Check if repo is modified, or is an SVN repo at all, etc..
            client.update(local_dir, revision)
        else:
            print("Checking out " + self.repo_path + " revision " + self.revision + " to " + local_dir)
            client.checkout(self.repo_path,
                            local_dir,
                            revision=revision)

    #FIXME: Rename to print for python3 and return instead of print
    def dump_config(self):
        print("Repo path : " + self.repo_path + \
            "\nRevision  : " + self.revision)

    #FIXME: Remove
    def repo_info(self):
        client = pysvn.Client()
        print(client.info('../cores_dl/or1200').url)
