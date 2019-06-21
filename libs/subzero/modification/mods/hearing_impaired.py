# coding=utf-8
import re

from subzero.modification.mods import SubtitleTextModification, empty_line_post_processors, EmptyEntryError, TAG
from subzero.modification.processors.re_processor import NReProcessor
from subzero.modification import registry


class FullBracketEntryProcessor(NReProcessor):
    def process(self, content, debug=False, **kwargs):
        entry = kwargs.get("entry")
        if entry:
            rep_content = super(FullBracketEntryProcessor, self).process(entry, debug=debug, **kwargs)
            if not rep_content.strip():
                raise EmptyEntryError()
        return content


class HearingImpaired(SubtitleTextModification):
    identifier = "remove_HI"
    description = "Remove Hearing Impaired tags"
    exclusive = True
    order = 20

    long_description = "Removes tags, text and characters from subtitles that are meant for hearing impaired people"

    processors = [
        # full bracket entry, single or multiline; starting with brackets and ending with brackets
        FullBracketEntryProcessor(re.compile(ur'(?sux)^-?%(t)s[([].+(?=[^)\]]{3,}).+[)\]]%(t)s$' % {"t": TAG}),
                                  "", name="HI_brackets_full"),

        # uppercase text before colon (at least 3 uppercase chars); at start or after a sentence,
        # possibly with a dash in front; ignore anything ending with a quote
        NReProcessor(re.compile(ur'(?u)(?:(?<=^)|(?<=[.\-!?\"\']))([\s\->~]*(?=[A-ZÀ-Ž&+]\s*[A-ZÀ-Ž&+]\s*[A-ZÀ-Ž&+])'
                                ur'[A-zÀ-ž-_0-9\s\"\'&+()\[\],:]+:(?![\"\'’ʼ❜‘‛”“‟„])(?:\s+|$))(?![0-9])'), "",
                     name="HI_before_colon_caps"),

        # any text before colon (at least 3 chars); at start or after a sentence,
        # possibly with a dash in front; try not breaking actual sentences with a colon at the end by not matching if
        # a space is inside the text; ignore anything ending with a quote
        NReProcessor(re.compile(ur'(?u)(?:(?<=^)|(?<=[.\-!?\"]))([\s\->~]*((?=[A-zÀ-ž&+]\s*[A-zÀ-ž&+]\s*[A-zÀ-ž&+])'
                                ur'[A-zÀ-ž-_0-9\s\"\'&+()\[\]]+:)(?![\"’ʼ❜‘‛”“‟„])\s*)(?![0-9])'),
                     lambda match:
                     match.group(1) if (match.group(2).count(" ") > 0 or match.group(1).count("-") > 0)
                     else "" if not match.group(1).startswith(" ") else " ",
                     name="HI_before_colon_noncaps"),

        # brackets (only remove if at least 3 chars in brackets)
        NReProcessor(re.compile(ur'(?sux)-?%(t)s[([][^([)\]]+?(?=[A-zÀ-ž"\'.]{3,})[^([)\]]+[)\]][\s:]*%(t)s' %
                                {"t": TAG}), "", name="HI_brackets"),

        #NReProcessor(re.compile(ur'(?sux)-?%(t)s[([]%(t)s(?=[A-zÀ-ž"\'.]{3,})[^([)\]]+%(t)s$' % {"t": TAG}),
        #             "", name="HI_bracket_open_start"),

        #NReProcessor(re.compile(ur'(?sux)-?%(t)s(?=[A-zÀ-ž"\'.]{3,})[^([)\]]+[)\]][\s:]*%(t)s' % {"t": TAG}), "",
        #             name="HI_bracket_open_end"),

        # text before colon (and possible dash in front), max 11 chars after the first whitespace (if any)
        # NReProcessor(re.compile(r'(?u)(^[A-z\-\'"_]+[\w\s]{0,11}:[^0-9{2}][\s]*)'), "", name="HI_before_colon"),

        # starting text before colon (at least 3 chars)
        #NReProcessor(re.compile(ur'(?u)(\b|^)([\s-]*(?=[A-zÀ-ž-_0-9"\']{3,})[A-zÀ-ž-_0-9"\']+:\s*)'), "",
        #             name="HI_before_colon"),


        # text in brackets at start, after optional dash, before colon or at end of line
        # fixme: may be too aggressive
        #NReProcessor(re.compile(ur'(?um)(^-?\s?[([][A-zÀ-ž-_\s]{3,}[)\]](?:(?=$)|:\s*))'), "",
        #             name="HI_brackets_special"),

        # all caps line (at least 4 consecutive uppercase chars)
        NReProcessor(re.compile(ur'(?u)(^(?=.*[A-ZÀ-Ž&+]{4,})[A-ZÀ-Ž-_\s&+]+$)'), "", name="HI_all_caps",
                     supported=lambda p: not p.only_uppercase),

        # remove MAN:
        NReProcessor(re.compile(ur'(?suxi)(\b(?:WO)MAN:\s*)'), "", name="HI_remove_man"),

        # dash in front
        # NReProcessor(re.compile(r'(?u)^\s*-\s*'), "", name="HI_starting_dash"),

        # all caps at start before new sentence
        NReProcessor(re.compile(ur'(?u)^(?=[A-ZÀ-Ž]{4,})[A-ZÀ-Ž-_\s]+\s([A-ZÀ-Ž][a-zà-ž].+)'), r"\1",
                     name="HI_starting_upper_then_sentence", supported=lambda p: not p.only_uppercase),
    ]

    post_processors = empty_line_post_processors
    last_processors = [
        # remove music symbols
        NReProcessor(re.compile(ur'(?u)(^%(t)s[*#¶♫♪\s]*%(t)s[*#¶♫♪\s]+%(t)s[*#¶♫♪\s]*%(t)s$)' % {"t": TAG}),
                     "", name="HI_music_symbols_only"),

        # remove music entries
        NReProcessor(re.compile(ur'(?ums)(^[-\s>~]*[♫♪]+\s*.+|.+\s*[♫♪]+\s*$)'),
                     "", name="HI_music"),
    ]


registry.register(HearingImpaired)
