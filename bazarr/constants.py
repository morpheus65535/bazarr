# coding=utf-8

import os
import re

# set Bazarr user-agent used to make requests
headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}

# hearing-impaired detection regex
hi_regex = re.compile(r'[*¶♫♪].{3,}[*¶♫♪]|[\[\(\{].{3,}[\]\)\}](?<!{\\an\d})')
