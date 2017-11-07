from get_general_settings import *

import os
import subprocess

def check_and_apply_update():
    result =  subprocess.check_output(["git", "pull", '--dry-run', 'origin', branch], stderr=subprocess.STDOUT).split('\n')
    print result

    if result[2] is not '':
        subprocess.check_output(["git", "pull", 'origin', branch])
        os.execlp('python', 'python ' + os.path.join(os.path.dirname(__file__), 'bazarr.py'))

check_and_apply_update()
