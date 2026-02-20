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
                                        stderr=subprocess.PIPE)
            out_codepage, err_codepage = codepage.communicate()
            enc_raw = out_codepage.decode('ascii', errors='ignore').split(':')[-1].strip().rstrip('.')
            encoding = 'cp' + enc_raw if enc_raw.isdigit() else enc_raw

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, encoding=encoding)
        # wait for the process to terminate
        out, err = process.communicate()

        out = out.replace('\n', ' ').replace('\r', ' ')

    except Exception as e:
        logging.error(f'BAZARR Post-processing failed for file {path}: {repr(e)}')
    else:
        if err:
            parsed_err = err.replace('\n', ' ').replace('\r', ' ')
            logging.error(f'BAZARR Post-processing result for file {path}: {parsed_err}')
        elif out == "":
            logging.info(
                f'BAZARR Post-processing result for file {path}: Nothing returned from command execution')
        else:
            logging.info(f'BAZARR Post-processing result for file {path}: {out}')
