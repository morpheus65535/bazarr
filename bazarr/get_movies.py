# coding=utf-8

import logging

from list_subtitles import movies_full_scan_subtitles


def update_all_movies():
    movies_full_scan_subtitles()
    logging.info('BAZARR All existing movie subtitles indexed from disk.')
