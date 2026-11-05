import pytest
from subliminal.utils import sanitize as subliminal_sanitize
from subliminal_patch.utils import sanitize as patch_sanitize


@pytest.mark.parametrize("sanitize_fn", [subliminal_sanitize, patch_sanitize])
class TestSanitize:
    def test_accent_normalization(self, sanitize_fn):
        assert sanitize_fn("Pokémon") == "pokemon"
        assert sanitize_fn("Amélie") == "amelie"
        assert sanitize_fn("Señor") == "senor"
        assert sanitize_fn("Über") == "uber"
        assert sanitize_fn("Käse") == "kase"
        assert sanitize_fn("Garçon") == "garcon"
        assert sanitize_fn("Noël") == "noel"

    def test_title_accent_matching(self, sanitize_fn):
        t1 = "Pokémon the Movie: I Choose You!"
        t2 = "Pokemon the Movie I Choose You"
        assert sanitize_fn(t1) == sanitize_fn(t2) == "pokemon the movie i choose you"

    def test_punctuation_stripping(self, sanitize_fn):
        assert sanitize_fn("What If...?") == "what if"
        assert sanitize_fn("Je te choisis !") == "je te choisis"
        assert sanitize_fn("Spider-Man: No Way Home") == "spider man no way home"
        assert sanitize_fn("Mamma Mia! Here We Go Again") == "mamma mia here we go again"
        assert sanitize_fn("¡Yo te elijo!") == "yo te elijo"
        assert sanitize_fn("¿Cómo estás?") == "como estas"

    def test_fullwidth_punctuation_normalization(self, sanitize_fn):
        t1 = "精靈寶可夢：就決定是你了！"
        t2 = "精靈寶可夢 就決定是你了"
        assert sanitize_fn(t1) == sanitize_fn(t2) == "精靈寶可夢 就決定是你了"

    def test_non_latin_scripts_preservation(self, sanitize_fn):
        assert sanitize_fn("Покемон 20: Я выбираю тебя!") == "покемон 20 я выбираю тебя"
        assert sanitize_fn("чай, ещё") == "чай ещё"
        assert sanitize_fn("ポケットモンスター きみにきめた！") == "ポケットモンスター きみにきめた"

    def test_quotes_removal(self, sanitize_fn):
        assert sanitize_fn("It's a Wonderful Life") == "its a wonderful life"
        assert sanitize_fn("Ocean’s Eleven") == "oceans eleven"

    def test_ignore_characters(self, sanitize_fn):
        assert sanitize_fn("Spider-Man: No Way", ignore_characters={":"}) == "spider man: no way"

    def test_invalid_types(self, sanitize_fn):
        assert sanitize_fn(None) is None
        assert sanitize_fn(123) is None
        assert sanitize_fn([]) is None


def test_custom_default_characters():
    assert patch_sanitize("Show/Name.2020", default_characters={"/"}) == "show name.2020"
