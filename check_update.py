from get_general_settings import *

import git

g = git.cmd.Git(os.path.dirname(__file__))
g.pull('origin ' + branch + ' --dry-run')

print g