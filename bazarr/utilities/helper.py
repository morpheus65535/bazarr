# coding=utf-8

import os
import logging
import hashlib

from charset_normalizer import detect
from bs4 import UnicodeDammit

from app.config import settings


def check_credentials(user, pw, request, log_success=True):
    forwarded_for_ip_addr = request.environ.get('HTTP_X_FORWARDED_FOR')
    real_ip_addr = request.environ.get('HTTP_X_REAL_IP')
    ip_addr = forwarded_for_ip_addr or real_ip_addr or request.remote_addr
    username = settings.auth.username
    password = settings.auth.password
    if hashlib.md5(f"{pw}".encode('utf-8')).hexdigest() == password and user == username:
        if log_success:
            logging.info(f'Successful authentication from {ip_addr} for user {user}')
        return True
    else:
        logging.info(f'Failed authentication from {ip_addr} for user {user}')
        return False


def get_subtitle_destination_folder():
    fld_custom = str(settings.general.subfolder_custom).strip() if (settings.general.subfolder_custom and
                                                                    settings.general.subfolder != 'current') else None
    return fld_custom


def get_target_folder(file_path):
    subfolder = settings.general.subfolder
    fld_custom = str(settings.general.subfolder_custom).strip() \
        if settings.general.subfolder_custom else None

    if subfolder != "current" and fld_custom:
        # specific subFolder requested, create it if it doesn't exist
        fld_base = os.path.split(file_path)[0]

        if subfolder == "absolute":
            # absolute folder
            fld = fld_custom
        elif subfolder == "relative":
            fld = os.path.join(fld_base, fld_custom)
        else:
            fld = None

        fld = force_unicode(fld)

        if not os.path.isdir(fld):
            try:
                os.makedirs(fld)
            except Exception:
                logging.error(f'BAZARR is unable to create directory to save subtitles: {fld}')
                fld = None
    else:
        fld = None

    return fld


def force_unicode(s):
    """
    Ensure a string is unicode, not encoded; used for enforcing file paths to be unicode upon saving a subtitle,
    to prevent encoding issues when saving a subtitle to a non-ascii path.
    :param s: string
    :return: unicode string
    """
    if not isinstance(s, str):
        try:
            s = s.decode("utf-8")
        except UnicodeDecodeError:
            t = detect(s)['encoding']
            try:
                s = s.decode(t)
            except UnicodeDecodeError:
                s = UnicodeDammit(s).unicode_markup
    return s
