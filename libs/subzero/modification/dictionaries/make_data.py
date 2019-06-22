# coding=utf-8

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
            u"°x°": u"%",
            u"compiete": u"complete",
            u"Âs": u"'s",
            u"ÃÂs": u"'s",
            u"a/ion": u"ation",
            u"at/on": u"ation",
            u"l/an": u"lian",
            u"lljust": u"ll just",
            u" L ": u" I ",
            u" l ": u" I ",
            u"'sjust": u"'s just",
            u"'tjust": u"'t just",
            u"\";": u"'s",
        },
        "WholeWords": {
            u"I'11": u"I'll",
            u"III'll": u"I'll",
            u"Tun": u"Run",
            u"pan'": u"part",
            u"al'": u"at",
            u"a re": u"are",
            u"wail'": u"wait",
            u"he)'": u"hey",
            u"he)\"": u"hey",
            u"He)'": u"Hey",
            u"He)\"": u"Hey",
            u"He)’": u"Hey",
            u"Yea h": u"Yeah",
            u"yea h": u"yeah",
            u"h is": u"his",
            u" 're ": u"'re ",
            u"LAst": u"Last",
            u"forthis": u"for this",
            u"Ls": u"Is",
            u"Iam": u"I am",
            u"Ican": u"I can",
        },
        "PartialLines": {
            u"L know": u"I know",
            u"L should": u"I should",
            u"L do": u"I do",
            u"L would": u"I would",
            u"L could": u"I could",
            u"L can": u"I can",
            u"L happen": u"I happen",
            u"L might": u"I might",
            u"L have ": u"I have",
            u"L had": u"I had",
            u"L want": u"I want",
            u"L was": u"I was",
            u"L am": u"I am",
            u"L will": u"I will",
            u"L suggest": u"I suggest",
            u"L think": u"I think",
            u"L reckon": u"I reckon",
            u"L like": u"I like",
            u"L love": u"I love",
            u"L don't": u"I don't",
            u"L didn't": u"I didn't",
            u"L wasn't": u"I wasnt't",
            u"L haven't": u"I haven't",
            u"L couldn't": u"I couldn't",
            u"L won't": u"I won't",
            u"H i": u"Hi",
        },
        "BeginLines": {
            u"l ": u"I ",
            u"L ": u"I ",
        }
    },
    "nld": {
        "PartialWordsAlways": {
            u"ט": u"è",
            u"י": u"é",
            u"כ": u"ë",
            u"צ": u"ë",
            u"ן": u"ï",
            u"ף": u"ó",
            u"א": u"à",
            u"Iֻ": u"I",
            u"č": u"è",
            u"פ": u"o",
            u"ם": u"i",
        },
    },
    "swe": {
        "PartialWordsAlways": {
            u"ĺ": u"å",
            u"Ĺ": u"Å",
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
                    ("WholeWords", "Word", lambda d: (ur"(?um)(\b|^)(?:" + u"|".join([re.escape(k) for k in d.keys()])
                                                      + ur')(\b|$)') if d else None),
                    ("PartialWordsAlways", "WordPart", None),
                    ("PartialLines", "LinePart", lambda d: (ur"(?um)(?:(?<=\s)|(?<=^)|(?<=\b))(?:" +
                                                            u"|".join([re.escape(k) for k in d.keys()]) +
                                                            ur")(?:(?=\s)|(?=$)|(?=\b))") if d else None),
                    ("BeginLines", "Beginning", lambda d: (ur"(?um)^(?:"+u"|".join([re.escape(k) for k in d.keys()])
                                                           + ur')') if d else None),
                    ("EndLines", "Ending", lambda d: (ur"(?um)(?:" + u"|".join([re.escape(k) for k in d.keys()]) +
                                                      ur")$") if d else None,),
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
