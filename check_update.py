from get_general_settings import *

import os
import subprocess
result =  subprocess.check_output(["git", "pull", '--dry-run', 'origin', branch], stderr=subprocess.STDOUT).split('\n')

if len(result) > 2:
    subprocess.check_output(["git", "pull", 'origin', branch])
    os.execlp('python', os.path.join(os.path.dirname(__file__), 'bazarr.py'))
