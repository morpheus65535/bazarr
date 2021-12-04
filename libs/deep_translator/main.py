"""Console script for deep_translator."""

import click
from .google_trans import GoogleTranslator
from .mymemory import MyMemoryTranslator
from .deepl import DeepL
from .qcri import QCRI
from .linguee import LingueeTranslator
from .pons import PonsTranslator
from .yandex import YandexTranslator
from .microsoft import MicrosoftTranslator
from .papago import PapagoTranslator

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
@click.group()
def cli():
    pass

@cli.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@click.argument('translator', required=True, default='google', type=str)
@click.option("--source", "-src", required=True, type=str, help="source language to translate from")
@click.option("--target", "-tgt", required=True, type=str, help="target language to translate to")
@click.option("--text", "-txt", type=str,required = True,prompt="Enter the text you want to translate",help="text you want to translate")
@click.option("--api-key",type=str,help="required for DeepL, QCRI, Yandex, Microsoft and Papago translators")
def translate(translator, source, target, text, api_key):
    """
    Use TRANSLATOR to translate source material into another language.
    \f
    Directory function to send arguments to the correct translator.
    @param translator: translator name parsed from terminal arguments
    @return: None
    """
    api_key_required = ["deepl", "qcri", "yandex", "microsoft", "papago"]
    if translator in api_key_required and not api_key:
        click.echo(
            "This translator requires an api key provided through --api-key")
    else:
        pass

    if translator == "google":
        translator = GoogleTranslator(source=source, target=target)
    elif translator == "mymemory":
        translator = MyMemoryTranslator(source=source, target=target)
    elif translator == "deepl":
        translator = DeepL(source=source, target=target, api_key=api_key)
    elif translator == "qcri":
        translator = QCRI(source=source, target=target, api_key=api_key)
    elif translator == "linguee":
        translator = LingueeTranslator(source=source, target=target)
    elif translator == "pons":
        translator = PonsTranslator(source=source, target=target)
    elif translator == "yandex":
        translator = YandexTranslator(
            source=source,
            target=target,
            api_key=api_key)
    elif translator == "microsoft":
        translator = MicrosoftTranslator(
            source=source,
            target=target,
            api_key=api_key)
    elif translator == "papago":
        translator = PapagoTranslator(
            source=source,
            target=target,
            api_key=api_key)
    else:
        raise AttributeError("The given translator is not supported.")

    res = translator.translate(text)
    click.echo(f" | Translation from {source} to {target} |")
    click.echo(f"Translated text: \n {res}")
    return 0

@cli.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@click.argument('translator')
@click.argument('api_key', required=False)
def languages(translator, api_key):
    """
    Retrieve the list of available languages from the given translator.
    @param translator: Translator given by the user.
    @param api_key: Optional API key given by the user. Required for some translators.
    @return: None
    """
    translator = translator.lower()
    api_key_required = ["deepl", "qcri", "yandex", "microsoft", "papago"]
    if translator in api_key_required and not api_key:
        click.echo("This translator requires an api key provided through --api-key")
    else:
        pass

    if translator == "google":
        translator = GoogleTranslator
    elif translator == "mymemory":
        translator = MyMemoryTranslator
    elif translator == "qcri":
        translator = QCRI(api_key=api_key)
    elif translator == "linguee":
        translator = LingueeTranslator
    elif translator == "pons":
        translator = PonsTranslator
    elif translator == "yandex":
        translator = YandexTranslator(api_key=api_key)
    elif translator == "microsoft":
        translator = MicrosoftTranslator(api_key=api_key)
    elif translator == "papago":
        translator = PapagoTranslator(api_key=api_key)
    else:
        raise AttributeError("The given translator is not supported.")

    supported_languages = translator.get_supported_languages(as_dict=True)
    click.echo(f"Languages supported by '{translator}' are :")
    for k, v in supported_languages.items():
        click.echo(f"|- {k}: {v}")
    return 0

@cli.command()
def list():
    """Lists available translators."""
    click.echo("Available translators include: Google, MyMemory, QCRI, Linguee, Pons, Yandex, Microsoft (Bing), and Papago.")
    return 0

if __name__ == "__main__":
    cli()
