# coding: utf-8 
from __future__ import unicode_literals

from get_general_settings import *

import git

g = git.cmd.Git(os.path.dirname(__file__))
print g.pull('--dry-run', 'origin', branch)
