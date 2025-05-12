"""
# Gemini SRT Translator
    A tool to translate subtitles using Google Generative AI.

## Usage:

### Translate Subtitles
    You can translate subtitles using the `translate` command:
    ```
    import gemini_srt_translator as gst

    gst.gemini_api_key = "your_gemini_api_key_here"
    gst.target_language = "French"
    gst.input_file = "subtitle.srt"

    gst.translate()
    ```
    This will translate the subtitles in the `subtitle.srt` file to French.

### List Models
    You can list the available models using the `listmodels` command:
    ```
    import gemini_srt_translator as gst

    gst.gemini_api_key = "your_gemini_api_key_here"
    gst.listmodels()
    ```
    This will print a list of available models to the console.

"""

from .main import GeminiSRTTranslator

gemini_api_key: str = None
gemini_api_key2: str = None
target_language: str = None
input_file: str = None
output_file: str = None
start_line: int = None
description: str = None
model_name: str = None
batch_size: int = None
free_quota: bool = None
use_colors: bool = None
error_log: bool = None


def translate():
    """
    ## Translates a subtitle file using the Gemini API.
        This function configures the genai library with the provided Gemini API key
        and translates the dialogues in the subtitle file to the target language.
        The translated dialogues are then written to a new subtitle file.

    Example:
    ```
    import gemini_srt_translator as gst

    # Your Gemini API key
    gst.gemini_api_key = "your_gemini_api_key_here"

    # Target language for translation
    gst.target_language = "French"

    # Path to the subtitle file to translate
    gst.input_file = "subtitle.srt"

    # (Optional) Gemini API key 2 for additional quota
    gst.gemini_api_key2 = "your_gemini_api_key2_here"

    # (Optional) Path to save the translated subtitle file
    gst.output_file = "translated_subtitle.srt"

    # (Optional) Line number to start translation from
    gst.start_line = 120

    # (Optional) Additional description of the translation task
    gst.description = "This subtitle is from a TV Series called 'Friends'."

    # (Optional) Model name to use for translation (default: "gemini-2.0-flash")
    gst.model_name = "gemini-2.0-flash"

    # (Optional) Batch size for translation (default: 30)
    gst.batch_size = 30

    # (Optional) Use free quota for translation (default: True)
    gst.free_quota = True

    # (Optional) Skip package upgrade check (default: False)
    gst.skip_upgrade = True

    # (Optional) Use colors in the output (default: True)
    gst.use_colors = True

    # (Optional) Enable error logging (default: False)
    gst.error_log = True

    gst.translate()
    ```
    Raises:
        Exception: If the Gemini API key is not provided.
        Exception: If the target language is not provided.
        Exception: If the subtitle file is not provided.
    """
    params = {
        "gemini_api_key": gemini_api_key,
        "gemini_api_key2": gemini_api_key2,
        "target_language": target_language,
        "input_file": input_file,
        "output_file": output_file,
        "start_line": start_line,
        "description": description,
        "model_name": model_name,
        "batch_size": batch_size,
        "free_quota": free_quota,
        "use_colors": use_colors,
        "error_log": error_log,
    }

    # Filter out None values
    filtered_params = {k: v for k, v in params.items() if v is not None}
    translator = GeminiSRTTranslator(**filtered_params)
    translator.translate()
