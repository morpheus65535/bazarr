# coding=utf-8

import logging

from list_subtitles import series_full_scan_subtitles


def update_all_episodes():
    series_full_scan_subtitles()
    logging.info('BAZARR All existing episode subtitles indexed from disk.')
