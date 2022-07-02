# coding=utf-8
# fmt: off

import os
import logging
import subprocess

from locale import getpreferredencoding


def postprocessing(command, path):
    try:
        encoding = getpreferredencoding()
        if os.name == 'nt':
            codepage = subprocess.Popen("chcp", shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, encoding=getpreferredencoding())
            # wait for the process to terminate
            out_codepage, err_codepage = codepage.communicate()
            encoding = out_codepage.split(':')[-1].strip()

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, encoding=encoding)
        # wait for the process to terminate
        out, err = process.communicate()

        out = out.replace('\n', ' ').replace('\r', ' ')

    except Exception as e:
        logging.error('BAZARR Post-processing failed for file ' + path + ' : ' + repr(e))
    else:
        if out == "":
            logging.info(
                'BAZARR Post-processing result for file ' + path + ' : Nothing returned from command execution')
        elif err:
            logging.error(
                'BAZARR Post-processing result for file ' + path + ' : ' + err.replace('\n', ' ').replace('\r', ' '))
        else:
            logging.info('BAZARR Post-processing result for file ' + path + ' : ' + out)
