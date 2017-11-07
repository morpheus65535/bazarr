from get_general_settings import *

import git
import subprocess
print subprocess.check_output(["git", "pull", '--dry-run', '--quiet', 'origin', branch], stderr=subprocess.STDOUT)
