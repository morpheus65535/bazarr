from __future__ import absolute_import
import logging
import time
from datetime import timedelta

from requests import Session

from requests.exceptions import JSONDecodeError
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.providers import Provider
from subliminal import __short_version__
from subliminal.exceptions import ConfigurationError
from subzero.language import Language
from subliminal.video import Episode, Movie

from babelfish.exceptions import LanguageReverseError

import ffmpeg
import functools
from pycountry import languages

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

def set_log_level(newLevel="INFO"):
    newLevel = newLevel.upper()
    # print(f'WhisperAI log level changing from {logging._levelToName[logger.getEffectiveLevel()]} to {newLevel}')
    logger.setLevel(getattr(logging, newLevel))

# initialize to default above
set_log_level()

# ffmpeg uses the older ISO 639-2 code when extracting audio streams based on language
# if we give it the newer ISO 639-3 code it can't find that audio stream by name because it's different
# for example it wants 'ger' instead of 'deu' for the German language
#                   or 'fre' instead of 'fra' for the French language
def get_ISO_639_2_code(iso639_3_code):
    # find the language using ISO 639-3 code
    language = languages.get(alpha_3=iso639_3_code)
    # get the ISO 639-2 code or use the original input if there isn't a match
    iso639_2_code = language.bibliographic if language and hasattr(language, 'bibliographic') else iso639_3_code
    logger.debug(f"ffmpeg using language code '{iso639_2_code}' (instead of '{iso639_3_code}')")
    return iso639_2_code

@functools.lru_cache(2)
def encode_audio_stream(path, ffmpeg_path, audio_stream_language=None):
    logger.debug("Encoding audio stream to WAV with ffmpeg")

    try:
        # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
        inp = ffmpeg.input(path, threads=0)
        if audio_stream_language:
            # There is more than one audio stream, so pick the requested one by name
            # Use the ISO 639-2 code if available
            audio_stream_language = get_ISO_639_2_code(audio_stream_language)
            logger.debug(f"Whisper will use the '{audio_stream_language}' audio stream for {path}")
            # 0 = Pick first stream in case there are multiple language streams of the same language,
            # otherwise ffmpeg will try to combine multiple streams, but our output format doesn't support that.
            # The first stream is probably the correct one, as later streams are usually commentaries
            lang_map = f"0:m:language:{audio_stream_language}"
        else:
            # there is only one stream, so just use that one
            lang_map = ""
        out, _ = (
            inp.output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=16000, af="aresample=async=1")
            .global_args("-map", lang_map)
            .run(cmd=[ffmpeg_path, "-nostdin"], capture_stdout=True, capture_stderr=True) 
        )

    except ffmpeg.Error as e:
        logger.warning(f"ffmpeg failed to load audio: {e.stderr.decode()}")
        return None

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
    return None

def language_from_alpha3(lang):
    name = Language(lang).name
    return name

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
        # Construct unique id otherwise provider pool will think 
        # subtitles are all the same and drop all except the first one
        # This is important for language profiles with more than one language
        return f"{self.video.original_name}_{self.task}_{str(self.language)}"

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

    video_types = (Episode, Movie)

    def __init__(self, endpoint=None, response=None, timeout=None, ffmpeg_path=None, pass_video_name=None, loglevel=None):
        set_log_level(loglevel)
        if not endpoint:
            raise ConfigurationError('Whisper Web Service Endpoint must be provided')

        if not response:
            raise ConfigurationError('Whisper Web Service Connection/response timeout  must be provided')

        if not timeout:
            raise ConfigurationError('Whisper Web Service Transcription/translation timeout must be provided')

        if not ffmpeg_path:
            raise ConfigurationError("ffmpeg path must be provided")
        
        if pass_video_name is None:
            raise ConfigurationError('Whisper Web Service Pass Video Name option must be provided')

        self.endpoint = endpoint.rstrip("/")
        self.response = int(response)
        self.timeout = int(timeout)
        self.session = None
        self.ffmpeg_path = ffmpeg_path
        self.pass_video_name = pass_video_name

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__

    def terminate(self):
        self.session.close()


    @functools.lru_cache(2048)
    def detect_language(self, path) -> Language:
        out = encode_audio_stream(path, self.ffmpeg_path)

        if out == None:
            logger.info(f"Whisper cannot detect language of {path} because of missing/bad audio track")
            return None
        video_name = path if self.pass_video_name else None

        r = self.session.post(f"{self.endpoint}/detect-language",
                              params={'encode': 'false', 'video_file': {video_name}},
                              files={'audio_file': out},
                              timeout=(self.response, self.timeout))
        
        try:
            results = r.json()
        except JSONDecodeError:
            results = {}

        if len(results) == 0:
            logger.info(f"Whisper returned empty response when detecting language")
            return None

        logger.debug(f"Whisper detected language of {path} as {results['detected_language']}")

        return whisper_get_language(results["language_code"], results["detected_language"])

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
            if detected_lang == None:
                sub.task = "error"
                # tell the user what is wrong
                sub.release_info = "bad/missing audio track - cannot transcribe"
                return sub

            if detected_lang != language:
                sub.task = "translate"

            sub.audio_language = detected_lang.alpha3

        if sub.task == "translate":
            if language.alpha3 != "eng":
                logger.debug(f"Translation only possible from {language} to English")
                return None
            
        # tell the user what we are about to do
        sub.release_info = f"{sub.task} {language_from_alpha3(sub.audio_language)} audio -> {language_from_alpha3(language.alpha3)} SRT"
        logger.debug(f"Whisper query: ({video.original_path}): {sub.audio_language} -> {language.alpha3} [TASK: {sub.task}]")

        return sub

    def list_subtitles(self, video, languages):
        subtitles = [self.query(l, video) for l in languages]
        return [s for s in subtitles if s is not None]

    def download_subtitle(self, subtitle: WhisperAISubtitle):
        # Invoke Whisper through the API. This may take a long time depending on the file.
        # TODO: This loads the entire file into memory, find a good way to stream the file in chunks

        out = None
        if subtitle.task != "error":
            out = encode_audio_stream(subtitle.video.original_path, self.ffmpeg_path, subtitle.force_audio_stream)
        if out == None:
            logger.info(f"Whisper cannot process {subtitle.video.original_path} because of missing/bad audio track")
            subtitle.content = None
            return  

        logger.debug(f'Audio stream length (in WAV format) is {len(out):,} bytes')

        if subtitle.task == "transcribe":
            output_language = subtitle.audio_language
        else:
            output_language = "eng"

        input_language = whisper_get_language_reverse(subtitle.audio_language)
        if input_language is None:
            if output_language == "eng":
                # guess that audio track is mislabelled English and let whisper try to transcribe it
                input_language = "en"
                subtitle.task = "transcribe"
                logger.info(f"Whisper treating unsupported audio track language: '{subtitle.audio_language}' as English")
            else:
                logger.info(f"Whisper cannot process {subtitle.video.original_path} because of unsupported audio track language: '{subtitle.audio_language}'")
                subtitle.content = None
                return
        
        logger.info(f'Starting WhisperAI {subtitle.task} to {language_from_alpha3(output_language)} for {subtitle.video.original_path}')
        startTime = time.time()
        video_name = subtitle.video.original_path if self.pass_video_name else None

        r = self.session.post(f"{self.endpoint}/asr",
                              params={'task': subtitle.task, 'language': input_language, 'output': 'srt', 'encode': 'false',
                                      'video_file': {video_name}},
                              files={'audio_file': out},
                              timeout=(self.response, self.timeout))
                              
        endTime = time.time()
        elapsedTime = timedelta(seconds=round(endTime - startTime))

        # for debugging, log if anything got returned
        subtitle_length = len(r.content)
        logger.debug(f'Returned subtitle length is {subtitle_length:,} bytes')
        subtitle_length = min(subtitle_length, 1000)
        if subtitle_length > 0:
            logger.debug(f'First {subtitle_length} bytes of subtitle: {r.content[0:subtitle_length]}')

        logger.info(f'Completed WhisperAI {subtitle.task} to {language_from_alpha3(output_language)} in {elapsedTime} for {subtitle.video.original_path}')

        subtitle.content = r.content
