from google.genai.types import HarmBlockThreshold, HarmCategory, SafetySetting


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


def get_safety_settings() -> list[SafetySetting]:
    """
    Get the safety settings for the translation model.
    """
    return [
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
    ]
