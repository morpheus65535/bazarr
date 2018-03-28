import subprocess
from subprocess import check_output
import logging
import os
import sys

try:
    logging.info('Installing Python modules required for Bazarr...')

    command = sys.executable + ' -m pip --disable-pip-version-check -q -q install -r ' + os.path.join(os.path.dirname(__file__), 'requirements.txt')

    if os.name == 'nt':
        codepage = check_output("chcp", shell=True, stderr=subprocess.STDOUT)
        encoding = codepage.split(':')[-1].strip()

    process = check_output(command, shell=True, stderr=subprocess.STDOUT)

    if os.name == 'nt':
        process = process.decode(encoding)
except:
    logging.error('Unable to install requirements using command line PIP. Is PIP installed and included in system path?')
    pass
else:
    if process == "":
        logging.info('Required Python modules installed if missing.')
    else:
        for line in process.splitlines():
            logging.error(line)