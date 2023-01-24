# coding=utf-8

import os
import re

# set Bazarr user-agent used to make requests
headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}

# hearing-impaired detection regex
hi_regex = re.compile(r'[*¶♫♪].{3,}[*¶♫♪]|[\[\(\{].{3,}[\]\)\}](?<!{\\an\d})')

# sync request timeouts
radarr_http_timeout = int(os.getenv("RADARR_HTTP_TIMEOUT", "60"))
sonarr_http_timeout = int(os.getenv("SONARR_HTTP_TIMEOUT", "60"))
