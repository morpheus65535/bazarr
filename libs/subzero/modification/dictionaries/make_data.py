# coding=utf-8
from __future__ import absolute_import
from __future__ import unicode_literals

import re
import os
import pprint
from collections import OrderedDict

from bs4 import BeautifulSoup

TEMPLATE = """\
import re
from collections import OrderedDict
data = """

TEMPLATE_END = """\

for lang, grps in data.iteritems():
    for grp in grps.iterkeys():
        if data[lang][grp]["pattern"]:
            data[lang][grp]["pattern"] = re.compile(data[lang][grp]["pattern"])
"""


SZ_FIX_DATA = {
    "eng": {
        "PartialWordsAlways": {
            "°x°": "%",
            "compiete": "complete",
            "Âs": "'s",
            "ÃÂs": "'s",
            "a/ion": "ation",
            "at/on": "ation",
            "l/an": "lian",
            "lljust": "ll just",
            " L ": " I ",
            " l ": " I ",
            "'sjust": "'s just",
            "'tjust": "'t just",
            "\";": "'s",
        },
        "WholeWords": {
            "I'11": "I'll",
            "III'll": "I'll",
            "Tun": "Run",
            "pan'": "part",
            "al'": "at",
            "a re": "are",
            "wail'": "wait",
            "he)'": "hey",
            "he)\"": "hey",
            "He)'": "Hey",
            "He)\"": "Hey",
            "He)’": "Hey",
            "Yea h": "Yeah",
            "yea h": "yeah",
            "h is": "his",
            " 're ": "'re ",
            "LAst": "Last",
            "forthis": "for this",
            "Ls": "Is",
            "Iam": "I am",
            "Ican": "I can",
        },
        "PartialLines": {
            "L know": "I know",
            "L should": "I should",
            "L do": "I do",
            "L would": "I would",
            "L could": "I could",
            "L can": "I can",
            "L happen": "I happen",
            "L might": "I might",
            "L have ": "I have",
            "L had": "I had",
            "L want": "I want",
            "L was": "I was",
            "L am": "I am",
            "L will": "I will",
            "L suggest": "I suggest",
            "L think": "I think",
            "L reckon": "I reckon",
            "L like": "I like",
            "L love": "I love",
            "L don't": "I don't",
            "L didn't": "I didn't",
            "L wasn't": "I wasnt't",
            "L haven't": "I haven't",
            "L couldn't": "I couldn't",
            "L won't": "I won't",
            "H i": "Hi",
        },
        "BeginLines": {
            "l ": "I ",
            "L ": "I ",
        }
    },
    "nld": {
        "PartialWordsAlways": {
            "ט": "è",
            "י": "é",
            "כ": "ë",
            "צ": "ë",
            "ן": "ï",
            "ף": "ó",
            "א": "à",
            "Iֻ": "I",
            "č": "è",
            "פ": "o",
            "ם": "i",
        },
    },
    "swe": {
        "PartialWordsAlways": {
            "ĺ": "å",
            "Ĺ": "Å",
        }
    }
}

SZ_FIX_DATA_GLOBAL = {
}

if __name__ == "__main__":
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    xml_dir = os.path.join(cur_dir, "xml")
    file_list = os.listdir(xml_dir)

    data = {}

    for fn in file_list:
        if fn.endswith("_OCRFixReplaceList.xml"):
            lang = fn.split("_")[0]
            soup = BeautifulSoup(open(os.path.join(xml_dir, fn)), "xml")

            fetch_data = (
                    # group, item_name, pattern
                    ("WholeLines", "Line", None),
                    ("WholeWords", "Word", lambda d: (r"(?um)(\b|^)(?:" + "|".join([re.escape(k) for k in list(d.keys())])
                                                      + r')(\b|$)') if d else None),
                    ("PartialWordsAlways", "WordPart", None),
                    ("PartialLines", "LinePart", lambda d: (r"(?um)(?:(?<=\s)|(?<=^)|(?<=\b))(?:" +
                                                            "|".join([re.escape(k) for k in list(d.keys())]) +
                                                            r")(?:(?=\s)|(?=$)|(?=\b))") if d else None),
                    ("BeginLines", "Beginning", lambda d: (r"(?um)^(?:"+"|".join([re.escape(k) for k in list(d.keys())])
                                                           + r')') if d else None),
                    ("EndLines", "Ending", lambda d: (r"(?um)(?:" + "|".join([re.escape(k) for k in list(d.keys())]) +
                                                      r")$") if d else None,),
            )

            data[lang] = dict((grp, {"data": OrderedDict(), "pattern": None}) for grp, item_name, pattern in fetch_data)

            for grp, item_name, pattern in fetch_data:
                for grp_data in soup.find_all(grp):
                    for line in grp_data.find_all(item_name):
                        data[lang][grp]["data"][line["from"]] = line["to"]

                # add our own dictionaries
                if lang in SZ_FIX_DATA and grp in SZ_FIX_DATA[lang]:
                    data[lang][grp]["data"].update(SZ_FIX_DATA[lang][grp])

                if grp in SZ_FIX_DATA_GLOBAL:
                    data[lang][grp]["data"].update(SZ_FIX_DATA_GLOBAL[grp])

                if pattern:
                    data[lang][grp]["pattern"] = pattern(data[lang][grp]["data"])

    f = open(os.path.join(cur_dir, "data.py"), "w+")
    f.write(TEMPLATE)
    f.write(pprint.pformat(data, width=1))
    f.write(TEMPLATE_END)
    f.close()
