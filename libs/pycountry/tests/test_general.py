import gettext
import re

import pytest

import pycountry
import pycountry.db


@pytest.fixture(autouse=True, scope="session")
def logging():
    import logging

    logging.basicConfig(level=logging.DEBUG)


def test_country_list():
    assert len(pycountry.countries) == 249
    assert isinstance(list(pycountry.countries)[0], pycountry.db.Data)


def test_country_fuzzy_search():
    results = pycountry.countries.search_fuzzy("England")
    assert len(results) == 1
    assert results[0] == pycountry.countries.get(alpha_2="GB")

    # Match alternative names exactly and thus NL ends up with
    # "Sint Maarten" before SX with "Sint Maarten (Dutch part)"
    results = pycountry.countries.search_fuzzy("Sint Maarten")
    assert len(results) == 2
    assert results[0] == pycountry.countries.get(alpha_2="NL")
    assert results[1] == pycountry.countries.get(alpha_2="SX")

    # Match with accents removed, first a country with a partial match in the
    # country name, then a country with multiple subdivision partial matches,
    # and then a country with a single subdivision match.
    results = pycountry.countries.search_fuzzy("Cote")
    assert len(results) == 3
    assert results[0] == pycountry.countries.get(alpha_2="CI")
    assert results[1] == pycountry.countries.get(alpha_2="FR")
    assert results[2] == pycountry.countries.get(alpha_2="HN")

    # A somewhat carefully balanced point system allows for a (bias-based)
    # graceful sorting of common substrings being used in multiple matches:
    results = pycountry.countries.search_fuzzy("New")
    assert results[0] == pycountry.countries.get(alpha_2="NC")
    assert results[1] == pycountry.countries.get(alpha_2="NZ")
    assert results[2] == pycountry.countries.get(alpha_2="PG")
    assert results[3] == pycountry.countries.get(alpha_2="GB")
    assert results[4] == pycountry.countries.get(alpha_2="US")
    assert results[5] == pycountry.countries.get(alpha_2="CA")
    assert results[6] == pycountry.countries.get(alpha_2="AU")
    assert results[7] == pycountry.countries.get(alpha_2="BS")
    assert results[8] == pycountry.countries.get(alpha_2="TW")
    assert results[9] == pycountry.countries.get(alpha_2="MH")

    # bug #34, likely about capitalization that was broken
    results = pycountry.countries.search_fuzzy("united states of america")
    assert len(results) == 1
    assert results[0] == pycountry.countries.get(alpha_2="US")


def test_historic_country_fuzzy_search():
    results = pycountry.historic_countries.search_fuzzy("burma")
    assert len(results) == 1
    assert results[0] == pycountry.historic_countries.get(alpha_4="BUMM")


def test_germany_has_all_attributes():
    germany = pycountry.countries.get(alpha_2="DE")
    assert germany.alpha_2 == "DE"
    assert germany.alpha_3 == "DEU"
    assert germany.numeric == "276"
    assert germany.name == "Germany"
    assert germany.official_name == "Federal Republic of Germany"


def test_subdivisions_directly_accessible():
    assert len(pycountry.subdivisions) == 5127
    assert isinstance(list(pycountry.subdivisions)[0], pycountry.db.Data)

    de_st = pycountry.subdivisions.get(code="DE-ST")
    assert de_st.code == "DE-ST"
    assert de_st.name == "Sachsen-Anhalt"
    assert de_st.type == "Land"
    assert de_st.parent is None
    assert de_st.parent_code is None
    assert de_st.country is pycountry.countries.get(alpha_2="DE")


def test_subdivisions_have_subdivision_as_parent():
    fr_01 = pycountry.subdivisions.get(code="FR-01")
    assert fr_01.code == "FR-01"
    assert fr_01.name == "Ain"
    assert fr_01.type == "Metropolitan department"
    assert fr_01.parent_code == "FR-ARA"
    assert fr_01.parent is pycountry.subdivisions.get(code="FR-ARA")
    assert fr_01.parent.name == "Auvergne-Rhône-Alpes"


def test_query_subdivisions_of_country():
    assert len(pycountry.subdivisions.get(country_code="DE")) == 16
    assert len(pycountry.subdivisions.get(country_code="US")) == 57


def test_scripts():
    assert len(pycountry.scripts) == 182
    assert isinstance(list(pycountry.scripts)[0], pycountry.db.Data)

    latin = pycountry.scripts.get(name="Latin")
    assert latin.alpha_4 == "Latn"
    assert latin.name == "Latin"
    assert latin.numeric == "215"


def test_currencies():
    assert len(pycountry.currencies) == 170
    assert isinstance(list(pycountry.currencies)[0], pycountry.db.Data)

    argentine_peso = pycountry.currencies.get(alpha_3="ARS")
    assert argentine_peso.alpha_3 == "ARS"
    assert argentine_peso.name == "Argentine Peso"
    assert argentine_peso.numeric == "032"


def test_languages():
    assert len(pycountry.languages) == 7847
    assert isinstance(list(pycountry.languages)[0], pycountry.db.Data)

    aragonese = pycountry.languages.get(alpha_2="an")
    assert aragonese.alpha_2 == "an"
    assert aragonese.alpha_3 == "arg"
    assert aragonese.name == "Aragonese"

    bengali = pycountry.languages.get(alpha_2="bn")
    assert bengali.name == "Bengali"
    assert bengali.common_name == "Bangla"

    # this tests the slow search path in lookup()
    bengali2 = pycountry.languages.lookup("bAngLa")
    assert bengali2 == bengali


def test_language_families():
    assert len(pycountry.language_families) == 115
    assert isinstance(list(pycountry.language_families)[0], pycountry.db.Data)

    aragonese = pycountry.languages.get(alpha_3="arg")
    assert aragonese.alpha_3 == "arg"
    assert aragonese.name == "Aragonese"


def test_locales():
    german = gettext.translation(
        "iso3166", pycountry.LOCALES_DIR, languages=["de"]
    )
    german.install()
    assert _("Germany") == "Deutschland"


def test_removed_countries():
    ussr = pycountry.historic_countries.get(alpha_3="SUN")
    assert isinstance(ussr, pycountry.db.Data)
    assert ussr.alpha_4 == "SUHH"
    assert ussr.alpha_3 == "SUN"
    assert ussr.name == "USSR, Union of Soviet Socialist Republics"
    assert ussr.withdrawal_date == "1992-08-30"


def test_repr():
    assert re.match(
        "Country\\(alpha_2=u?'DE', "
        "alpha_3=u?'DEU', "
        "flag='..', "
        "name=u?'Germany', "
        "numeric=u?'276', "
        "official_name=u?'Federal Republic of Germany'\\)",
        repr(pycountry.countries.get(alpha_2="DE")),
    )


def test_dir():
    germany = pycountry.countries.get(alpha_2="DE")
    for n in "alpha_2", "alpha_3", "name", "numeric", "official_name":
        assert n in dir(germany)


def test_get():
    c = pycountry.countries
    with pytest.raises(TypeError):
        c.get(alpha_2="DE", alpha_3="DEU")
    assert c.get(alpha_2="DE") == c.get(alpha_3="DEU")
    assert c.get(alpha_2="Foo") is None
    tracer = object()
    assert c.get(alpha_2="Foo", default=tracer) is tracer


def test_lookup():
    c = pycountry.countries
    g = c.get(alpha_2="DE")
    assert g == c.get(alpha_2="de")
    assert g == c.lookup("de")
    assert g == c.lookup("DEU")
    assert g == c.lookup("276")
    assert g == c.lookup("germany")
    assert g == c.lookup("Federal Republic of Germany")
    # try a generated field
    bqaq = pycountry.historic_countries.get(alpha_4="BQAQ")
    assert bqaq == pycountry.historic_countries.lookup("atb")
    german = pycountry.languages.get(alpha_2="de")
    assert german == pycountry.languages.lookup("De")
    euro = pycountry.currencies.get(alpha_3="EUR")
    assert euro == pycountry.currencies.lookup("euro")
    latin = pycountry.scripts.get(name="Latin")
    assert latin == pycountry.scripts.lookup("latn")
    fr_ara = pycountry.subdivisions.get(code="FR-ARA")
    assert fr_ara == pycountry.subdivisions.lookup("fr-ara")
    with pytest.raises(LookupError):
        pycountry.countries.lookup("bogus country")
    with pytest.raises(LookupError):
        pycountry.countries.lookup(12345)
    with pytest.raises(LookupError):
        pycountry.countries.get(alpha_2=12345)


def test_subdivision_parent():
    s = pycountry.subdivisions
    sd = s.get(code="CV-BV")
    assert sd.parent_code == "CV-B"
    assert sd.parent is s.get(code=sd.parent_code)


def test_subdivision_missing_code_raises_keyerror():
    s = pycountry.subdivisions
    assert s.get(code="US-ZZ") is None


def test_subdivision_empty_list():
    s = pycountry.subdivisions
    assert len(s.get(country_code="DE")) == 16
    assert len(s.get(country_code="JE")) == 0
    assert s.get(country_code="FOOBAR") is None


def test_has_version_attribute():
    assert pycountry.__version__ != "n/a"
    assert len(pycountry.__version__) >= 5
    assert "." in pycountry.__version__
