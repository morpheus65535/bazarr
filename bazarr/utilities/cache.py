# coding=utf-8

import os
import logging
import datetime
import glob
from typing import cast

from subliminal import region as subliminal_cache_region
from subzero.cache_backends.file import SZFileBackend

from app.get_args import args
from app.jobs_queue import jobs_queue


def cache_maintenance(job_id: int | None = None, wait_for_completion: bool = False) -> None:
    """
    Perform maintenance on the subliminal cache and archive cache files.

    When no job identifier is supplied, the function schedules itself as a job
    in the jobs queue and returns immediately (or after the job completes,
    depending on the wait flag). When invoked with a job identifier, it
    inspects every file in the main subliminal cache backend and every
    ``*.archive`` file in the configuration directory, removing those whose
    modification time exceeds the configured validity period (14 days for the
    main cache, 4 days for archive packs). Once the cleanup is finished, the
    name of the associated job in the jobs queue is updated to reflect the
    completed state.

    :param job_id: Identifier of the job under which this maintenance run is
        tracked. When ``None``, a new job is queued instead of running the
        maintenance directly.
    :param wait_for_completion: Whether to block until the queued maintenance
        job has finished. Only relevant when no job identifier is provided.
    :return: None
    """
    if not job_id:
        jobs_queue.add_job_from_function("Performing Cache Maintenance", is_progress=False,
                                         wait_for_completion=wait_for_completion)
        return

    main_cache_validity = 14  # days
    pack_cache_validity = 4  # days

    logging.debug("BAZARR Running cache maintenance")
    now = datetime.datetime.now()

    def _remove_expired(path: str, expiry: int) -> None:
        """
        Remove a cache file if it is older than the given expiry period.

        The file's modification time is compared against the current time;
        when the file has exceeded the allowed age in days it is deleted
        from the filesystem. Any failure to delete the file is logged at
        debug level and otherwise ignored.

        :param path: Filesystem path to the cache file to check and
            potentially remove.
        :param expiry: Maximum allowed age of the file, in days, before it
            is considered expired.
        :return: None
        """
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        if mtime + datetime.timedelta(days=expiry) < now:
            try:
                os.remove(path)
            except (IOError, OSError):
                logging.debug("Couldn't remove cache file: %s", os.path.basename(path))

    # main cache
    for fn in cast(SZFileBackend, subliminal_cache_region.backend).all_filenames:
        _remove_expired(fn, main_cache_validity)

    # archive cache
    for fn in glob.iglob(os.path.join(args.config_dir, "*.archive")):
        _remove_expired(fn, pack_cache_validity)

    jobs_queue.update_job_name(job_id=job_id, new_job_name="Performed Cache Maintenance")
