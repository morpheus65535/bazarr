import os
import time

from subzero.modification import SubtitleModifications

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "hi_music_long_drawing.ass")


def _remove_hi(content):
    mods = SubtitleModifications()
    mods.load(content=content, language=None)
    started = time.monotonic()
    mods.modify("remove_HI")
    return [event.text for event in mods.f], time.monotonic() - started


def test_remove_hi_long_ass_drawing_is_fast_and_kept():
    with open(SAMPLE_PATH, encoding="utf-8") as f:
        content = f.read()

    texts, elapsed = _remove_hi(content)

    # without the precheck the HI_music regex is quadratic on the ~30k chars drawing line and takes many seconds
    assert elapsed < 2
    assert texts[0] == "Normal dialogue line."
    assert texts[1] == "Who's there?"
    assert texts[2].startswith("{\\an7\\pos(0,0)") and texts[2].endswith("{\\p0}")
    assert texts[3] == "Another normal line."


def test_remove_hi_still_removes_music_entries():
    with open(SAMPLE_PATH, encoding="utf-8") as f:
        content = f.read()

    texts, _ = _remove_hi(content)

    assert not any("♪" in text for text in texts)
