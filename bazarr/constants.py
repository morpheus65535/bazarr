# coding=utf-8

import os

# set Bazarr user-agent used to make requests
HEADERS = {"User-Agent": os.environ["SZ_USER_AGENT"]}

# minimum file size for Bazarr to consider it a video
MINIMUM_VIDEO_SIZE = 20480

# maximum size for a subtitles file
MAXIMUM_SUBTITLE_SIZE = 1 * 1024 * 1024

# Language profile HI modes: "True" (require HI), "False" (normal, accept either),
# "Excluded" (exclude HI entirely). Historically: "only"/"also"/"never" → collapsed to
# "True"/"False" at startup; "Excluded" is a new explicit value, distinct from the retired "never".
HI_EXCLUDED = "Excluded"
