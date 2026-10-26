from subzero.modification import SubtitleModifications


def _remove_hi(*texts):
    """Return the text of each entry after remove_HI, or None if the entry was removed."""
    content = "".join("%d\n00:00:%02d,000 --> 00:00:%02d,500\n%s\n\n" % (i + 1, i, i, text)
                      for i, text in enumerate(texts))
    mods = SubtitleModifications()
    mods.load(content=content, language=None)
    mods.modify("remove_HI")
    texts_by_start = {event.start: event.text for event in mods.f}
    return [texts_by_start.get(i * 1000) for i in range(len(texts))]


def test_remove_hi_keeps_dialogue_between_brackets():
    assert _remove_hi(
        "Well [laughs] I can't believe it. [sighs]",
        "[SIGHS] Thanks. [CHUCKLES]",
        "[INHALES SHARPLY] I\nlost track. [CHUCKLES]",
        "-[exhales] George.\n-[door locks]",
    ) == [
        "Well I can't believe it.",
        "Thanks.",
        "I\\Nlost track.",
        "George.",
    ]


def test_remove_hi_removes_brackets_with_a_dash():
    assert _remove_hi(
        "[walkie-talkie beeps] Copy that.",
        "- Ah...\n- [high-pitched ringing]",
    ) == [
        "Copy that.",
        "- Ah...",
    ]


def test_remove_hi_still_removes_bracket_only_entries():
    assert _remove_hi(
        "Normal dialogue line.",
        "[door creaks]",
        "[laughs]\n[sighs]",
        "-[laughs]\n-[sighs]",
        "(dramatic music\nplaying)",
        "[man speaking (in French)]",
        "[door creaks] Who's there?",
    ) == [
        "Normal dialogue line.",
        None,
        None,
        None,
        None,
        None,
        "Who's there?",
    ]
