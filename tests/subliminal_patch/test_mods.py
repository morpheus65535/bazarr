import pytest
import os
from subliminal_patch import Subtitle


@pytest.fixture
def test_file(data):
    return os.path.join(data, "subs_for_mods.srt")


def test_apply_mods_remove_hi(languages, test_file):
    sub = Subtitle(languages["en"], mods=["remove_HI", "OCR_fixes"])
    with open(test_file, "rb") as f:
        sub.content = f.read()

    assert sub.get_modified_content(debug=True)
