# -*- coding: utf-8 -*-
from .ffprobe import refine_from_ffprobe
from .database import refine_from_db

registered = {"database": refine_from_db, "ffprobe": refine_from_ffprobe}
