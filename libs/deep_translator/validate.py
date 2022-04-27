from deep_translator.exceptions import NotValidLength, NotValidPayload


def is_empty(text: str) -> bool:
    return text == ""


def is_input_valid(text: str, min_chars: int = 0, max_chars: int = 5000) -> bool:
    """
    validate the target text to translate
    @param min_chars: min characters
    @param max_chars: max characters
    @param text: text to translate
    @return: bool
    """

    if not isinstance(text, str) or text.isdigit():
        raise NotValidPayload(text)
    if not min_chars <= len(text) < max_chars:
        raise NotValidLength(text, min_chars, max_chars)

    return True
