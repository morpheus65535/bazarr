# coding=utf-8
from babelfish import Language

from subliminal_patch.converters.subsource import SubsourceConverter


def test_convert_brazilian_portuguese():
    # pt-BR must map to the Brazilian name, not generic Portuguese. The mapping is
    # stored under the two-tuple key ('por', 'BR'), so convert() must look it up.
    converter = SubsourceConverter()
    language = Language("por", "BR")
    assert converter.convert(language.alpha3, language.country, language.script) == "Brazillian Portuguese"


def test_convert_plain_portuguese_still_works():
    converter = SubsourceConverter()
    assert converter.convert("por") == "Portuguese"


def test_convert_brazilian_portuguese_round_trip():
    converter = SubsourceConverter()
    assert converter.convert(*converter.reverse("Brazillian Portuguese")) == "Brazillian Portuguese"
