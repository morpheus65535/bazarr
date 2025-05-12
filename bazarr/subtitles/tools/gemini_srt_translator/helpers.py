def get_instruction(language: str, description: str) -> str:
    """
    Get the instruction for the translation model based on the target language.
    """
    instruction = f"""You are an assistant that translates subtitles to {language}.
You will receive the following JSON type:

class SubtitleObject(typing.TypedDict):
    index: str
    content: str

Request: list[SubtitleObject]

The 'index' key is the index of the subtitle dialog.
The 'content' key is the dialog to be translated.

The indices must remain the same in the response as in the request.
Dialogs must be translated as they are without any changes.
"""
    if description:
        instruction += "\nAdditional user instruction: '" + description + "'"
    return instruction