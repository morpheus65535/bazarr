from __future__ import absolute_import
import logging

from requests import Session

from subliminal_patch.subtitle import Subtitle
from subliminal_patch.providers import Provider
from subliminal import __short_version__
from subliminal.exceptions import ConfigurationError
from subzero.language import Language
from subliminal.video import Episode, Movie

from babelfish.exceptions import LanguageReverseError

import ffmpeg
import functools

# These are all the languages Whisper supports.
# from whisper.tokenizer import LANGUAGES

whisper_languages = {
    "en": "english",
    "zh": "chinese",
    "de": "german",
    "es": "spanish",
    "ru": "russian",
    "ko": "korean",
    "fr": "french",
    "ja": "japanese",
    "pt": "portuguese",
    "tr": "turkish",
    "pl": "polish",
    "ca": "catalan",
    "nl": "dutch",
    "ar": "arabic",
    "sv": "swedish",
    "it": "italian",
    "id": "indonesian",
    "hi": "hindi",
    "fi": "finnish",
    "vi": "vietnamese",
    "he": "hebrew",
    "uk": "ukrainian",
    "el": "greek",
    "ms": "malay",
    "cs": "czech",
    "ro": "romanian",
    "da": "danish",
    "hu": "hungarian",
    "ta": "tamil",
    "no": "norwegian",
    "th": "thai",
    "ur": "urdu",
    "hr": "croatian",
    "bg": "bulgarian",
    "lt": "lithuanian",
    "la": "latin",
    "mi": "maori",
    "ml": "malayalam",
    "cy": "welsh",
    "sk": "slovak",
    "te": "telugu",
    "fa": "persian",
    "lv": "latvian",
    "bn": "bengali",
    "sr": "serbian",
    "az": "azerbaijani",
    "sl": "slovenian",
    "kn": "kannada",
    "et": "estonian",
    "mk": "macedonian",
    "br": "breton",
    "eu": "basque",
    "is": "icelandic",
    "hy": "armenian",
    "ne": "nepali",
    "mn": "mongolian",
    "bs": "bosnian",
    "kk": "kazakh",
    "sq": "albanian",
    "sw": "swahili",
    "gl": "galician",
    "mr": "marathi",
    "pa": "punjabi",
    "si": "sinhala",
    "km": "khmer",
    "sn": "shona",
    "yo": "yoruba",
    "so": "somali",
    "af": "afrikaans",
    "oc": "occitan",
    "ka": "georgian",
    "be": "belarusian",
    "tg": "tajik",
    "sd": "sindhi",
    "gu": "gujarati",
    "am": "amharic",
    "yi": "yiddish",
    "lo": "lao",
    "uz": "uzbek",
    "fo": "faroese",
    "ht": "haitian creole",
    "ps": "pashto",
    "tk": "turkmen",
    "nn": "nynorsk",
    "mt": "maltese",
    "sa": "sanskrit",
    "lb": "luxembourgish",
    "my": "myanmar",
    "bo": "tibetan",
    "tl": "tagalog",
    "mg": "malagasy",
    "as": "assamese",
    "tt": "tatar",
    "haw": "hawaiian",
    "ln": "lingala",
    "ha": "hausa",
    "ba": "bashkir",
    "jw": "javanese",
    "su": "sundanese",
}

logger = logging.getLogger(__name__)


@functools.lru_cache(2)
def encode_audio_stream(path, audio_stream_language=None):
    logger.debug("Encoding audio stream to WAV with ffmpeg")

    try:
        # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
        inp = ffmpeg.input(path, threads=0)
        if audio_stream_language:
            logger.debug(f"Whisper will only use the {audio_stream_language} audio stream for {path}")
            inp = inp[f'a:m:language:{audio_stream_language}']

        out, _ = inp.output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=16000) \
                    .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)

    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

    logger.debug(f"Finished encoding audio stream in {path} with no errors")

    return out


def whisper_get_language(code, name):
    # Whisper uses an inconsistent mix of alpha2 and alpha3 language codes
    try:
        return Language.fromalpha2(code)
    except LanguageReverseError:
        return Language.fromname(name)


def whisper_get_language_reverse(alpha3):
    # Returns the whisper language code given an alpha3b language
    for wl in whisper_languages:
        lan = whisper_get_language(wl, whisper_languages[wl])
        if lan.alpha3 == alpha3:
            return wl
    raise ValueError


class WhisperAISubtitle(Subtitle):
    '''Whisper AI Subtitle.'''
    provider_name = 'whisperai'
    hash_verifiable = False

    def __init__(self, language, video):
        super(WhisperAISubtitle, self).__init__(language)

        self.video = video
        self.task = None
        self.audio_language = None
        self.force_audio_stream = None

    @property
    def id(self):
        return self.video.original_name

    def get_matches(self, video):
        matches = set()

        if isinstance(video, Episode):
            matches.update(["series", "season", "episode"])
        elif isinstance(video, Movie):
            matches.update(["title"])

        return matches


class WhisperAIProvider(Provider):
    '''Whisper AI Provider.'''

    languages = set()

    for lan in whisper_languages:
        languages.update({whisper_get_language(lan, whisper_languages[lan])})

    languages.update(set(Language.rebuild(lang, hi=True) for lang in languages))
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))

    video_types = (Episode, Movie)

    def __init__(self, endpoint=None, timeout=None):
        if not endpoint:
            raise ConfigurationError('Whisper Web Service Endpoint must be provided')

        if not timeout:
            raise ConfigurationError('Whisper Web Service Timeout must be provided')

        self.endpoint = endpoint
        self.timeout = int(timeout)
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__

    def terminate(self):
        self.session.close()


    @functools.lru_cache(2048)
    def detect_language(self, path) -> Language:
        out = encode_audio_stream(path)

        r = self.session.post(f"{self.endpoint}/detect-language",
                              params={'encode': 'false'},
                              files={'audio_file': out},
                              timeout=self.timeout)

        logger.info(f"Whisper detected language of {path} as {r.json()['detected_language']}")

        return whisper_get_language(r.json()["language_code"], r.json()["detected_language"])

    def query(self, language, video):
        if language not in self.languages:
            return None

        sub = WhisperAISubtitle(language, video)
        sub.task = "transcribe"

        if video.audio_languages and not (list(video.audio_languages)[0] == "und" and len(video.audio_languages) == 1):
            if language.alpha3 in video.audio_languages:
                sub.audio_language = language.alpha3
                if len(list(video.audio_languages)) > 1:
                    sub.force_audio_stream = language.alpha3
            else:
                sub.task = "translate"

                eligible_languages = list(video.audio_languages)
                if len(eligible_languages) > 1:
                    if "und" in eligible_languages:
                        eligible_languages.remove("und")
                sub.audio_language = eligible_languages[0]
        else:
            # We must detect the language manually
            detected_lang = self.detect_language(video.original_path)

            if detected_lang != language:
                sub.task = "translate"

            sub.audio_language = detected_lang.alpha3

        if sub.task == "translate":
            if language.alpha3 != "eng":
                logger.info(f"Translation only possible from {language} to English")
                return None

        logger.debug(f"Whisper ({video.original_path}): {sub.audio_language} -> {language.alpha3} [TASK: {sub.task}]")

        return sub

    def list_subtitles(self, video, languages):
        subtitles = [self.query(l, video) for l in languages]
        return [s for s in subtitles if s is not None]

    def download_subtitle(self, subtitle: WhisperAISubtitle):
        # Invoke Whisper through the API. This may take a long time depending on the file.
        # TODO: This loads the entire file into memory, find a good way to stream the file in chunks

        out = encode_audio_stream(subtitle.video.original_path, subtitle.force_audio_stream)

        r = self.session.post(f"{self.endpoint}/asr",
                              params={'task': subtitle.task, 'language': whisper_get_language_reverse(subtitle.audio_language), 'output': 'srt', 'encode': 'false'},
                              files={'audio_file': out},
                              timeout=self.timeout)

        subtitle.content = r.content
