# coding=utf-8
"""Unit tests for the ReverseRTL subtitle modification."""
import textwrap
import pytest

from subzero.language import Language
from subzero.modification import SubMod


def _apply(lines, lang="heb"):
    """Apply reverse_rtl to a list of subtitle lines and return results."""
    language = Language(lang)
    entries = "\n\n".join(
        f"{i}\n00:00:0{i},000 --> 00:00:0{i+1},000\n{line}"
        for i, line in enumerate(lines, 1)
    )
    sm = SubMod()
    sm.load(content=entries, language=language, mods=["reverse_rtl"])
    sm.modify("reverse_rtl")
    return [e.text for e in sm.f]


# ---------------------------------------------------------------------------
# Basic punctuation movement
# ---------------------------------------------------------------------------

def test_period_at_start():
    assert _apply([".הטקסט"]) == ["הטקסט."]


def test_question_mark_at_start():
    assert _apply(["?הטקסט"]) == ["הטקסט?"]


def test_exclamation_at_start():
    assert _apply(["!הטקסט"]) == ["הטקסט!"]


def test_colon_at_start():
    assert _apply([":הטקסט"]) == ["הטקסט:"]


def test_comma_at_start():
    # trailing space from ", " group is stripped by pysubs2
    assert _apply([", הטקסט"]) == ["הטקסט,"]


def test_ellipsis_at_start():
    assert _apply(["...הטקסט"]) == ["הטקסט..."]


def test_no_leading_punct_unchanged():
    assert _apply(["שלום"]) == ["שלום"]


# ---------------------------------------------------------------------------
# Trailing dialogue dash (Bug 1 fix: was moved to front, now stays at end)
# ---------------------------------------------------------------------------

def test_period_with_trailing_dash():
    assert _apply([".יו-"]) == ["יו.-"]


def test_period_with_trailing_dash_number_in_text():
    assert _apply([".כבר כמעט 10 עכשיו-"]) == ["כבר כמעט 10 עכשיו.-"]


def test_question_with_trailing_dash():
    assert _apply(["?בערך-"]) == ["בערך?-"]


def test_trailing_dash_only_unchanged():
    """A line with only a trailing dash and no leading punct must not be changed."""
    assert _apply(["אם היה לי סנט-"]) == ["אם היה לי סנט-"]


def test_period_comma_in_text_trailing_dash():
    """Period at start, comma mid-text, dash at end."""
    assert _apply([".כן, אבל אחיך בבידוד-"]) == ["כן, אבל אחיך בבידוד.-"]


# ---------------------------------------------------------------------------
# Closing HTML tag (Bug 3 fix: period now placed before </i>, not after)
# ---------------------------------------------------------------------------

def test_period_before_closing_tag():
    assert _apply([".הטקסט</i>"]) == ["הטקסט.</i>"]


def test_question_before_closing_tag():
    assert _apply(["?הטקסט</i>"]) == ["הטקסט?</i>"]


def test_period_before_closing_bold_tag():
    assert _apply([".הטקסט</b>"]) == ["הטקסט.</b>"]


# ---------------------------------------------------------------------------
# Opening HTML tag (Bug 2 fix: punct after <i> was ignored, now moved)
# ---------------------------------------------------------------------------

def test_period_after_opening_tag():
    assert _apply(["<i>.הטקסט"]) == ["<i>הטקסט."]


def test_colon_after_opening_tag():
    assert _apply(["<i>:האמת"]) == ["<i>האמת:"]


def test_comma_after_opening_tag():
    # trailing space from ", " group is stripped by pysubs2
    assert _apply(["<i>, הטקסט"]) == ["<i>הטקסט,"]


# ---------------------------------------------------------------------------
# Both opening and closing tags
# ---------------------------------------------------------------------------

def test_period_inside_both_tags():
    assert _apply(["<i>.הטקסט</i>"]) == ["<i>הטקסט.</i>"]


def test_question_inside_both_tags():
    assert _apply(["<i>?הטקסט</i>"]) == ["<i>הטקסט?</i>"]


def test_comma_inside_both_tags():
    assert _apply(["<i>, שליח פיצה</i>"]) == ["<i>שליח פיצה, </i>"]


def test_period_complex_text_inside_tags():
    assert _apply(["<i>.ברך אותי, אבי, כי חטאתי</i>"]) == [
        "<i>ברך אותי, אבי, כי חטאתי.</i>"
    ]


# ---------------------------------------------------------------------------
# Multi-line subtitle entries
# ---------------------------------------------------------------------------

def test_multiline_entry():
    """Each subtitle line is processed independently; both get reversed."""
    language = Language("heb")
    srt = textwrap.dedent("""\
        1
        00:00:01,000 --> 00:00:03,000
        .שורה ראשונה
        .שורה שנייה
    """)
    sm = SubMod()
    sm.load(content=srt, language=language, mods=["reverse_rtl"])
    sm.modify("reverse_rtl")
    lines = sm.f[0].text.split(r"\N")
    assert lines[0] == "שורה ראשונה."
    assert lines[1] == "שורה שנייה."


def test_real_file_entry():
    """Full entry: opening tag on one line, period+closing tag on next."""
    language = Language("heb")
    srt = textwrap.dedent("""\
        1
        00:00:01,000 --> 00:00:03,000
        <i>או אריסטו או אחד
        .מהאנשים הלבנים המתים האלה</i>
    """)
    sm = SubMod()
    sm.load(content=srt, language=language, mods=["reverse_rtl"])
    sm.modify("reverse_rtl")
    lines = sm.f[0].text.split(r"\N")
    assert lines[0] == "<i>או אריסטו או אחד"
    assert lines[1] == "מהאנשים הלבנים המתים האלה.</i>"


# ---------------------------------------------------------------------------
# Language gating: mod only applies to heb/ara/fas
# ---------------------------------------------------------------------------

def test_not_applied_to_english():
    result = _apply([".hello"], lang="eng")
    assert result == [".hello"]


def test_applied_to_arabic():
    assert _apply([".النص"], lang="ara") == ["النص."]


def test_applied_to_farsi():
    assert _apply([".متن"], lang="fas") == ["متن."]


# ---------------------------------------------------------------------------
# Arabic-specific tests
# ---------------------------------------------------------------------------

def test_arabic_period_at_start():
    assert _apply([".مرحباً"], lang="ara") == ["مرحباً."]


def test_arabic_question_mark_at_start():
    assert _apply(["?كيف حالك"], lang="ara") == ["كيف حالك?"]


def test_arabic_exclamation_at_start():
    assert _apply(["!شكراً"], lang="ara") == ["شكراً!"]


def test_arabic_trailing_dash_unchanged():
    assert _apply(["أنا لا أعرف-"], lang="ara") == ["أنا لا أعرف-"]


def test_arabic_period_with_trailing_dash():
    assert _apply([".هذا صحيح-"], lang="ara") == ["هذا صحيح.-"]


def test_arabic_period_before_closing_tag():
    assert _apply([".اليوم</i>"], lang="ara") == ["اليوم.</i>"]


def test_arabic_period_after_opening_tag():
    assert _apply(["<i>.اليوم"], lang="ara") == ["<i>اليوم."]


def test_arabic_period_inside_both_tags():
    assert _apply(["<i>.كيف حالك</i>"], lang="ara") == ["<i>كيف حالك.</i>"]


def test_arabic_comma_after_opening_tag():
    # space from ", " ends up before closing tag (pysubs2 keeps it inside tags)
    assert _apply(["<i>, هذا النص</i>"], lang="ara") == ["<i>هذا النص, </i>"]


def test_arabic_number_in_text():
    assert _apply([".الساعة 10 صباحاً-"], lang="ara") == ["الساعة 10 صباحاً.-"]


def test_arabic_multiline():
    language = Language("ara")
    srt = textwrap.dedent("""\
        1
        00:00:01,000 --> 00:00:03,000
        <i>هذا هو الخبر
        .مباشرةً من المصدر</i>
    """)
    sm = SubMod()
    sm.load(content=srt, language=language, mods=["reverse_rtl"])
    sm.modify("reverse_rtl")
    lines = sm.f[0].text.split(r"\N")
    assert lines[0] == "<i>هذا هو الخبر"
    assert lines[1] == "مباشرةً من المصدر.</i>"


def test_arabic_native_question_mark_not_reversed():
    """Arabic-specific ؟ is not in the char class — documents current limitation."""
    assert _apply(["؟كيف حالك"], lang="ara") == ["؟كيف حالك"]


def test_arabic_native_comma_not_reversed():
    """Arabic-specific ، is not in the char class — documents current limitation."""
    assert _apply(["،هذا النص"], lang="ara") == ["،هذا النص"]


# ---------------------------------------------------------------------------
# Farsi-specific tests
# ---------------------------------------------------------------------------

def test_farsi_period_at_start():
    assert _apply([".سلام"], lang="fas") == ["سلام."]


def test_farsi_question_mark_at_start():
    assert _apply(["?چطور هستید"], lang="fas") == ["چطور هستید?"]


def test_farsi_exclamation_at_start():
    assert _apply(["!ممنون"], lang="fas") == ["ممنون!"]


def test_farsi_trailing_dash_unchanged():
    assert _apply(["امروز خوب بود-"], lang="fas") == ["امروز خوب بود-"]


def test_farsi_period_with_trailing_dash():
    assert _apply([".این درست است-"], lang="fas") == ["این درست است.-"]


def test_farsi_period_before_closing_tag():
    assert _apply([".امروز</i>"], lang="fas") == ["امروز.</i>"]


def test_farsi_period_after_opening_tag():
    assert _apply(["<i>.امروز"], lang="fas") == ["<i>امروز."]


def test_farsi_period_inside_both_tags():
    assert _apply(["<i>.چطور هستید</i>"], lang="fas") == ["<i>چطور هستید.</i>"]


def test_farsi_number_in_text():
    assert _apply([".ساعت 10 صبح-"], lang="fas") == ["ساعت 10 صبح.-"]


def test_farsi_multiline():
    language = Language("fas")
    srt = textwrap.dedent("""\
        1
        00:00:01,000 --> 00:00:03,000
        <i>این یک خبر است
        .مستقیم از منبع</i>
    """)
    sm = SubMod()
    sm.load(content=srt, language=language, mods=["reverse_rtl"])
    sm.modify("reverse_rtl")
    lines = sm.f[0].text.split(r"\N")
    assert lines[0] == "<i>این یک خبر است"
    assert lines[1] == "مستقیم از منبع.</i>"


def test_farsi_native_question_mark_not_reversed():
    """Farsi-specific ؟ is not in the char class — documents current limitation."""
    assert _apply(["؟چطور هستید"], lang="fas") == ["؟چطور هستید"]


def test_farsi_native_comma_not_reversed():
    """Farsi-specific ، is not in the char class — documents current limitation."""
    assert _apply(["،این متن"], lang="fas") == ["،این متن"]
