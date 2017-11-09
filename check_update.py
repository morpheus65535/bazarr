from get_general_settings import *

import os
import subprocess

def check_and_apply_update():
    result =  subprocess.check_output(["git", "pull", '--dry-run', 'origin', branch], stderr=subprocess.STDOUT, shell=True, cwd=os.path.join(os.path.dirname(__file__)).split('\n')

    if result[2] is not '':
        subprocess.check_output(["git", "pull", 'origin', branch], shell=True, cwd=os.path.join(os.path.dirname(__file__))
        os.execlp('python', 'python ' + os.path.join(os.path.dirname(__file__), 'bazarr.py'))
