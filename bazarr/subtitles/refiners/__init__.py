# -*- coding: utf-8 -*-

from .ffprobe import refine_from_ffprobe
from .database import refine_from_db
from .arr_history import refine_from_arr_history
from .anidb import refine_from_anidb
from .anilist import refine_from_anilist

registered = {
    "database": refine_from_db,
    "ffprobe": refine_from_ffprobe,
    "arr_history": refine_from_arr_history,
    "anidb": refine_from_anidb,
    "anilist": refine_from_anilist, # Must run AFTER AniDB
}
