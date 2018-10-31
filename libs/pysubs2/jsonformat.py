from __future__ import unicode_literals, print_function

import json
from .common import Color, PY3
from .ssaevent import SSAEvent
from .ssastyle import SSAStyle
from .formatbase import FormatBase


class JSONFormat(FormatBase):
    @classmethod
    def guess_format(cls, text):
        if text.startswith("{\""):
            return "json"

    @classmethod
    def from_file(cls, subs, fp, format_, **kwargs):
        data = json.load(fp)

        subs.info.clear()
        subs.info.update(data["info"])

        subs.styles.clear()
        for name, fields in data["styles"].items():
            subs.styles[name] = sty = SSAStyle()
            for k, v in fields.items():
                if "color" in k:
                    setattr(sty, k, Color(*v))
                else:
                    setattr(sty, k, v)

        subs.events = [SSAEvent(**fields) for fields in data["events"]]

    @classmethod
    def to_file(cls, subs, fp, format_, **kwargs):
        data = {
            "info": dict(**subs.info),
            "styles": {name: sty.as_dict() for name, sty in subs.styles.items()},
            "events": [ev.as_dict() for ev in subs.events]
        }

        if PY3:
            json.dump(data, fp)
        else:
            text = json.dumps(data, fp)
            fp.write(unicode(text))
