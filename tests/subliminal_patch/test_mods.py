import pytest
import os
from subliminal_patch import Subtitle
from subzero.language import Language


@pytest.fixture
def test_file(data):
    return os.path.join(data, "subs_for_mods.srt")


def test_apply_mods_remove_hi(languages, test_file):
    sub = Subtitle(languages["en"], mods=["remove_HI", "OCR_fixes"])
    with open(test_file, "rb") as f:
        sub.content = f.read()

    assert sub.get_modified_content(debug=True)


def _srt(*lines):
    """Build a minimal SRT where every given line is its own entry."""
    entries = []
    for index, line in enumerate(lines, start=1):
        entries.append(f"{index}\n00:00:0{index},000 --> 00:00:0{index},900\n{line}\n")
    return "\n".join(entries)


def _remove_hi(content):
    """Run Remove HI over an SRT body and return the lines it kept."""
    sub = Subtitle(Language.fromietf("pl"), mods=["remove_HI"])
    sub.content = content.encode("utf-8")
    modified = sub.get_modified_content(format="srt")
    if isinstance(modified, bytes):
        modified = modified.decode("utf-8")
    return [line.strip() for line in modified.splitlines() if line.strip()]


def test_remove_hi_keeps_all_caps_line_with_latin_extended_uppercase():
    """An all-caps line must not be truncated to its tail.

    [a-zà-ž] spans U+00E0-U+017E, which also holds Latin Extended-A uppercase
    letters such as Ę (U+0118). With the previous plain r"\\1" replacement a
    word whose second letter was one of those counted as the start of a
    sentence, and the mod returned only what followed the last such word.
    """
    lines = _remove_hi(_srt("BUDA - KRÓLESTWO WĘGIER",
                            "SPRAWOWAŁ WŁADZĘ PRZEZ 68 LAT.",
                            "PARYŻ - CESARSTWO FRANCUSKIE"))

    assert "BUDA - KRÓLESTWO WĘGIER" in lines
    assert "SPRAWOWAŁ WŁADZĘ PRZEZ 68 LAT." in lines
    assert "PARYŻ - CESARSTWO FRANCUSKIE" in lines
    assert "WĘGIER" not in lines


def test_remove_hi_keeps_placard_and_sentence():
    """The processor still drops an all-caps placard before a normal sentence."""
    lines = _remove_hi(_srt("WARNING DANGER We must run.",
                            "SPANISH TITLE Eyebrow text",
                            "CHAPTER ONE It was raining."))

    assert "We must run." in lines
    assert "Eyebrow text" in lines
    assert "It was raining." in lines
    assert not any("WARNING" in line or "SPANISH" in line or "CHAPTER" in line
                   for line in lines)


def test_remove_hi_still_strips_speaker_prefix():
    """The mod as a whole strips a speaker prefix, via HI_before_colon_caps.

    HI_starting_upper_then_sentence does not handle this, but the change must
    not disturb the processor that does.
    """
    lines = _remove_hi(_srt("JAN: Idziemy", "ANNA: Zaczekaj!"))

    assert "Idziemy" in lines
    assert "Zaczekaj!" in lines
    assert not any("JAN" in line or "ANNA" in line for line in lines)


def test_remove_hi_still_drops_hearing_impaired_cues():
    """Bracketed cues remain HI_brackets' job and keep working."""
    lines = _remove_hi(_srt("[śmiech] Nie wierzę"))

    assert "Nie wierzę" in lines
    assert not any("śmiech" in line for line in lines)
