# -*- coding: utf-8 -*-

from .ffprobe import refine_from_ffprobe
from .database import refine_from_db
from .arr_history import refine_from_arr_history

registered = {
    "database": refine_from_db,
    "ffprobe": refine_from_ffprobe,
    "arr_history": refine_from_arr_history,
}
