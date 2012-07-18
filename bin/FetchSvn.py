import pysvn

client = pysvn.Client()
repo_root  = 'http://opencores.org/ocsvn/openrisc/openrisc'
repo_path  = 'trunk/or1200'
local_path = 'or1200_675'
client.checkout(os.path.join(repo_root,repo_path),
                local_path
                revision=675)
