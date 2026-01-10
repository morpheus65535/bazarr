from __future__ import absolute_import

import functools
import logging
import os
import time
from datetime import timedelta
import ffmpeg
from babelfish.exceptions import LanguageReverseError
from pycountry import languages as py_languages
from requests import Session
from requests.exceptions import JSONDecodeError
from subliminal import __short_version__
from subliminal.exceptions import ConfigurationError
from subliminal.video import Episode, Movie
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

# These are all the languages Whisper supports.
# from whisper.tokenizer import LANGUAGES

whisper_language_data = [
    ("en", "eng", "English"),
    ("zh", "zho", "Chinese"),
    ("de", "deu", "German"),
    ("es", "spa", "Spanish"),
    ("ru", "rus", "Russian"),
    ("ko", "kor", "Korean"),
    ("fr", "fra", "French"),
    ("ja", "jpn", "Japanese"),
    ("pt", "por", "Portuguese"),
    ("tr", "tur", "Turkish"),
    ("pl", "pol", "Polish"),
    ("ca", "cat", "Catalan"),
    ("nl", "nld", "Dutch"),
    ("ar", "ara", "Arabic"),
    ("sv", "swe", "Swedish"),
    ("it", "ita", "Italian"),
    ("id", "ind", "Indonesian"),
    ("hi", "hin", "Hindi"),
    ("fi", "fin", "Finnish"),
    ("vi", "vie", "Vietnamese"),
    ("he", "heb", "Hebrew"),
    ("uk", "ukr", "Ukrainian"),
    ("el", "ell", "Greek"),
    ("ms", "msa", "Malay"),
    ("cs", "ces", "Czech"),
    ("ro", "ron", "Romanian"),
    ("da", "dan", "Danish"),
    ("hu", "hun", "Hungarian"),
    ("ta", "tam", "Tamil"),
    ("no", "nor", "Norwegian"),
    ("th", "tha", "Thai"),
    ("ur", "urd", "Urdu"),
    ("hr", "hrv", "Croatian"),
    ("bg", "bul", "Bulgarian"),
    ("lt", "lit", "Lithuanian"),
    ("la", "lat", "Latin"),
    ("mi", "mri", "Maori"),
    ("ml", "mal", "Malayalam"),
    ("cy", "cym", "Welsh"),
    ("sk", "slk", "Slovak"),
    ("te", "tel", "Telugu"),
    ("fa", "fas", "Persian"),
    ("lv", "lav", "Latvian"),
    ("bn", "ben", "Bengali"),
    ("sr", "srp", "Serbian"),
    ("az", "aze", "Azerbaijani"),
    ("sl", "slv", "Slovenian"),
    ("kn", "kan", "Kannada"),
    ("et", "est", "Estonian"),
    ("mk", "mkd", "Macedonian"),
    ("br", "bre", "Breton"),
    ("eu", "eus", "Basque"),
    ("is", "isl", "Icelandic"),
    ("hy", "hye", "Armenian"),
    ("ne", "nep", "Nepali"),
    ("mn", "mon", "Mongolian"),
    ("bs", "bos", "Bosnian"),
    ("kk", "kaz", "Kazakh"),
    ("sq", "sqi", "Albanian"),
    ("sw", "swa", "Swahili"),
    ("gl", "glg", "Galician"),
    ("mr", "mar", "Marathi"),
    ("pa", "pan", "Punjabi"),
    ("si", "sin", "Sinhala"),
    ("km", "khm", "Khmer"),
    ("sn", "sna", "Shona"),
    ("yo", "yor", "Yoruba"),
    ("so", "som", "Somali"),
    ("af", "afr", "Afrikaans"),
    ("oc", "oci", "Occitan"),
    ("ka", "kat", "Georgian"),
    ("be", "bel", "Belarusian"),
    ("tg", "tgk", "Tajik"),
    ("sd", "snd", "Sindhi"),
    ("gu", "guj", "Gujarati"),
    ("am", "amh", "Amharic"),
    ("yi", "yid", "Yiddish"),
    ("lo", "lao", "Lao"),
    ("uz", "uzb", "Uzbek"),
    ("fo", "fao", "Faroese"),
    ("ht", "hat", "Haitian Creole"),
    ("ps", "pus", "Pashto"),
    ("tk", "tuk", "Turkmen"),
    ("nn", "nno", "Nynorsk"),
    ("mt", "mlt", "Maltese"),
    ("sa", "san", "Sanskrit"),
    ("lb", "ltz", "Luxembourgish"),
    ("my", "mya", "Myanmar"),
    ("bo", "bod", "Tibetan"),
    ("tl", "tgl", "Tagalog"),
    ("mg", "mlg", "Malagasy"),
    ("as", "asm", "Assamese"),
    ("tt", "tat", "Tatar"),
    ("haw", "haw", "Hawaiian"),
    ("ln", "lin", "Lingala"),
    ("ha", "hau", "Hausa"),
    ("ba", "bak", "Bashkir"),
    ("jw", "jav", "Javanese"),
    ("su", "sun", "Sundanese"),
    # these languages are not supported by whisper, but we map them below to existing similar languages
    ("gsw", "gsw", "Swiss German"),
    # ("und", "und", "Undefined"),
]

language_mapping = {
    "gsw": "deu",  # Swiss German -> German (ISO 639-3)
    "und": "eng",  # Undefined -> English
}

whisper_ambiguous_language_codes = [
    "alg",  # Algonquian languages (language family)
    "art",  # Artificial languages
    "ath",  # Athapascan languages (language family)
    "aus",  # Australian languages (language family)
    "mis",  # Miscellaneous languages
    "mul",  # Multiple languages
#    "qaa–qtz",  # Reserved for local use
    "sgn",  # Sign languages
    "und",  # Undetermined
    "zxx"   # No linguistic content
]

class LanguageManager:
    def __init__(self, language_data):
        """Initialize with language data as list of tuples (alpha2, alpha3, name)"""
        self.language_data = language_data
        self._build_indices()
    
    def _build_indices(self):
        """Build lookup dictionaries for quick access"""
        # Create indices for lookup by each code type
        self.by_alpha2 = {item[0]: item for item in self.language_data}
        self.by_alpha3 = {item[1]: item for item in self.language_data}
        self.by_name = {item[2]: item for item in self.language_data}
    
    def get_by_alpha2(self, code):
        """Get language tuple by alpha2 code"""
        return self.by_alpha2.get(code)
    
    def get_by_alpha3(self, code):
        """Get language tuple by alpha3 code"""
        return self.by_alpha3.get(code)
    
    def get_by_name(self, name):
        """Get language tuple by name"""
        return self.by_name.get(name.lower())
    
    def alpha2_to_alpha3(self, code):
        """Convert alpha2 to alpha3"""
        lang_tuple = self.get_by_alpha2(code)
        return lang_tuple[1] if lang_tuple else None
    
    def alpha3_to_alpha2(self, code):
        """Convert alpha3 to alpha2"""
        lang_tuple = self.get_by_alpha3(code)
        return lang_tuple[0] if lang_tuple else None
    
    def get_name(self, code, code_type="alpha3"):
        """Get language name from code"""
        if code_type == "alpha2":
            lang_tuple = self.get_by_alpha2(code)
        else:  # alpha3
            lang_tuple = self.get_by_alpha3(code)
        return lang_tuple[2] if lang_tuple else None
    
    def add_language_data(self, language_data):
        """Add a number of new language tuples to the data structure"""
        self.language_data.extend(language_data)
        # Update indices
        self._build_indices()
    
    def add_language(self, alpha2, alpha3, name):
        """Add a new language to the data structure"""
        new_lang = (alpha2, alpha3, name.lower())
        self.language_data.append(new_lang)
        # Update indices
        self._build_indices()
        return new_lang
    
    def get_all_language_names(self):
        """Return list of all language names"""
        return [item[2] for item in self.language_data]
    
    def get_all_alpha2(self):
        """Return list of all alpha2 codes"""
        return [item[0] for item in self.language_data]
    
    def get_all_alpha3(self):
        """Return list of all alpha3 codes"""
        return [item[1] for item in self.language_data]


class WhisperLanguageManager(LanguageManager):
    def __init__(self, language_data):
        super().__init__(language_data)

    def _get_language(self, code, name):
        # Handle 'und' language code explicitly
        if code == "und":
            logger.warning("Undefined language code detected")
            return None
        # Whisper uses an inconsistent mix of alpha2 and alpha3 language codes
        try:
            return Language.fromalpha2(code)
        except LanguageReverseError:
            try:
                return Language.fromname(name)
            except LanguageReverseError:
                logger.error(f"Could not convert Whisper language: {code} ({name})")
                return None
    
    def get_all_language_objects(self):
        """Return set of all Language objects"""
        # populate set of Language objects that are supoorted by Whisper
        return set(self._get_language(item[0], item[2]) for item in self.language_data)

    # ffmpeg uses the older ISO 639-2 code when extracting audio streams based on language
    # if we give it the newer ISO 639-3 code it can't find that audio stream by name because it's different
    # for example it wants 'ger' instead of 'deu' for the German language
    #                   or 'fre' instead of 'fra' for the French language
    def get_ISO_639_2_code(self, iso639_3_code):
        # find the language using ISO 639-3 code
        language = py_languages.get(alpha_3=iso639_3_code)
        # get the ISO 639-2 code or use the original input if there isn't a match
        iso639_2_code = language.bibliographic if language and hasattr(language, 'bibliographic') else iso639_3_code
        if iso639_2_code != iso639_3_code:
            logger.debug(f"ffmpeg using language code '{iso639_2_code}' (instead of '{iso639_3_code}')")
        return iso639_2_code


# Create language manager
wlm = WhisperLanguageManager(whisper_language_data)

logger = logging.getLogger(__name__)

def set_log_level(newLevel="INFO"):
    newLevel = newLevel.upper()
    # print(f'WhisperAI log level changing from {logging._levelToName[logger.getEffectiveLevel()]} to {newLevel}')
    logger.setLevel(getattr(logging, newLevel))

# initialize to default above
set_log_level()

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

    # these next two variables must be set for superclass or this provider will not be listed in subtitle search results
    languages = wlm.get_all_language_objects()
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

        # Use provided ambiguous language codes directly without fallback
        self.ambiguous_language_codes = whisper_ambiguous_language_codes
        logger.debug(f"Using ambiguous language codes: {self.ambiguous_language_codes}")

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__

    def terminate(self):
        self.session.close()

    @functools.lru_cache(2)
    def encode_audio_stream(self, path, ffmpeg_path, audio_stream_language=None):
        logger.debug("Encoding audio stream to WAV with ffmpeg")

        try:
            # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
            inp = ffmpeg.input(path, threads=0)
            if audio_stream_language:
                # There is more than one audio stream, so pick the requested one by name
                # Use the ISO 639-2 code if available
                audio_stream_language = wlm.get_ISO_639_2_code(audio_stream_language)
                logger.debug(f"Whisper will use the '{audio_stream_language}' audio stream for {path}")
                # 0 = Pick first stream in case there are multiple language streams of the same language,
                # otherwise ffmpeg will try to combine multiple streams, but our output format doesn't support that.
                # The first stream is probably the correct one, as later streams are usually commentaries
                lang_map = f"0:a:m:language:{audio_stream_language}"
                out = inp.output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=16000, af="aresample=async=1",
                                 map=lang_map)
            else:
                out = inp.output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=16000, af="aresample=async=1")

            start_time = time.time()
            out, _ = out.run(cmd=[ffmpeg_path, "-nostdin"], capture_stdout=True, capture_stderr=True) 
            elapsed_time = time.time() - start_time
            logger.debug(f'Finished encoding audio stream in {elapsed_time:.2f} seconds with no errors for "{path}"')           
            
        except ffmpeg.Error as e:
            logger.warning(f"ffmpeg failed to load audio: {e.stderr.decode()}")
            return None

        logger.debug(f'Audio stream length (in WAV format) is {len(out):,} bytes')

        return out

    @functools.lru_cache(2048)
    def detect_language(self, path) -> Language:
        out = self.encode_audio_stream(path, self.ffmpeg_path)

        if out is None:
            logger.info(f'WhisperAI cannot detect language of "{path}" because of missing/bad audio stream')
            return None

        try:
            video_name = path if self.pass_video_name else None
            r = self.session.post(f"{self.endpoint}/detect-language",
                                params={'encode': 'false', 'video_file': video_name},
                                files={'audio_file': out},
                                timeout=(self.response, self.timeout))
            results = r.json()
        except (JSONDecodeError):
            logger.error('Invalid JSON response in language detection')
            return None

        if not results.get("language_code"):
            logger.info('WhisperAI returned empty language code')
            return None

        # Explicitly handle 'und' from Whisper results
        if results["language_code"] == "und":
            logger.info('WhisperAI detected undefined language')
            return None

        logger.debug(f'Whisper detection raw results: {results}')
        return wlm._get_language(results["language_code"], results["detected_language"])

    def query(self, language, video):
        logger.debug(
            f'Whisper query request - Language: "{language.alpha3} '
            f'({wlm.get_name(language.alpha3)})" - File: "{os.path.basename(video.original_path)}"'
        )
        if language not in self.languages:
            logger.debug(f'Language {language.alpha3} not supported by Whisper')
            return None

        sub = WhisperAISubtitle(language, video)
        sub.task = "transcribe"

        # Handle undefined/no audio languages
        if not video.audio_languages:
            logger.debug('No audio language tags present, detection started')
            detected_lang = self.detect_language(video.original_path)
            if not detected_lang:
                sub.task = "error"
                sub.release_info = "Language detection failed"
                return sub
            
            logger.debug(f'Whisper detected audio language as "{detected_lang}"')

            # Apply language mapping after detection
            detected_alpha3 = detected_lang.alpha3
            if detected_alpha3 in language_mapping:
                detected_alpha3 = language_mapping[detected_alpha3]
                logger.debug(f'Mapped detected language {detected_lang} -> {detected_alpha3}')

            sub.audio_language = detected_alpha3

            if detected_alpha3 != language.alpha3:
                sub.task = "translate"
        else:
            # Existing audio language processing with mapping
            processed_languages = {}
            for lang in video.audio_languages:
                if lang in language_mapping:
                    logger.debug(f'Mapping audio language tag: {lang} -> {language_mapping[lang]}')
                mapped_lang = language_mapping.get(lang, lang)
                processed_languages[lang] = mapped_lang

            matched = False
            for original_lang, processed_lang in processed_languages.items():
                if language.alpha3 == processed_lang:
                    sub.audio_language = processed_lang
                    if len(video.audio_languages) > 1:
                        sub.force_audio_stream = original_lang
                    matched = True
                    break

            if not matched:
                sub.task = "translate"
                eligible_languages = [language_mapping.get(lang, lang) for lang in video.audio_languages]
                sub.audio_language = eligible_languages[0] if eligible_languages else None

            # Final validation
            if not sub.audio_language:
                sub.task = "error"
                sub.release_info = "No valid audio language determined"
                return sub
            else:
                # Handle case where audio language exists but may need verification
                # Only run language detection if original unmapped audio languages contain ambiguous codes
                original_ambiguous = any(
                    lang in self.ambiguous_language_codes
                    for lang in video.audio_languages
                )

                if original_ambiguous:
                    # Format audio languages with both code and name
                    formatted_audio_langs = [
                        f'"{lang}" ({wlm.get_name(lang)})'
                        for lang in video.audio_languages
                    ]
                    logger.debug(
                        f'Original unmapped audio language code(s) {", ".join(formatted_audio_langs)} '
                        f'matches "Ambiguous Languages Codes" list: {self.ambiguous_language_codes} - forcing detection!'
                    )

                    detected_lang = self.detect_language(video.original_path)
                    if detected_lang is None:
                        sub.task = "error"
                        sub.release_info = "Bad/missing audio track - cannot transcribe"
                        return sub

                    detected_alpha3 = detected_lang.alpha3
                    # Apply language mapping after detection
                    if detected_alpha3 in language_mapping:
                        detected_alpha3 = language_mapping[detected_alpha3]

                    sub.audio_language = detected_alpha3
                    if detected_alpha3 == language.alpha3:
                        sub.task = "transcribe"
                    else:
                        sub.task = "translate"

                    logger.debug(
                        f'WhisperAI detected audio language: {detected_lang.alpha3} ({wlm.get_name(detected_lang.alpha3)}) '
                        f'-> {sub.audio_language} ({wlm.get_name(sub.audio_language)}) - '
                        f'(requested subtitle language: {language.alpha3} ({wlm.get_name(language.alpha3)}))'
                    )
                else:
                    formatted_original = [
                        f'"{lang}" ({wlm.get_name(lang)})'
                        for lang in video.audio_languages
                    ]
                    logger.debug(
                        f'Using existing audio language tag: {sub.audio_language} ({wlm.get_name(sub.audio_language)}) '
                        f'(originally {formatted_original}) - skipping detection!'
                    )

        if sub.task == "translate":
            if language.alpha3 != "eng":
                logger.debug(
                    f'Cannot translate from {sub.audio_language} ({wlm.get_name(sub.audio_language)}) -> {language.alpha3} '
                    f'({wlm.get_name(language.alpha3)})!. - Only translations to English supported! - File: "{os.path.basename(sub.video.original_path)}"'
                )
                return None

        sub.release_info = f'{sub.task} {wlm.get_name(sub.audio_language)} audio -> {wlm.get_name(language.alpha3)} SRT'
        logger.debug(f'Whisper query result - Task: {sub.task} {sub.audio_language} -> {language.alpha3} for "({video.original_path})"')
        return sub

    def list_subtitles(self, video, languages):
        logger.debug(
            f'Languages requested from WhisperAI: "{", ".join(f"{lang.alpha3} ({wlm.get_name(lang.alpha3)})" for lang in languages)}"'
            f' - File: "{os.path.basename(video.original_path)}"'
        )
        subtitles = [self.query(lang, video) for lang in languages]
        return [s for s in subtitles if s is not None]

    def download_subtitle(self, subtitle: WhisperAISubtitle):
        # Invoke Whisper through the API. This may take a long time depending on the file.
        # TODO: This loads the entire file into memory, find a good way to stream the file in chunks

        if subtitle.task == "error":
            return

        out = self.encode_audio_stream(subtitle.video.original_path, self.ffmpeg_path, subtitle.force_audio_stream)
        if not out:
            logger.info(f"WhisperAI cannot process {subtitle.video.original_path} due to missing/bad audio track")
            subtitle.content = None
            return

        if subtitle.task == "transcribe":
            output_language = subtitle.audio_language
        else:
            output_language = "eng"

        # Convert mapped alpha3 to Whisper's alpha2 code
        input_language = wlm.alpha3_to_alpha2(subtitle.audio_language)
        if input_language is None:
            if output_language == "eng":
                input_language = "en"
                subtitle.task = "transcribe"
                logger.info(f"WhisperAI treating unsupported audio track language: '{subtitle.audio_language}' as English")
            else:
                logger.info(f"WhisperAI cannot process {subtitle.video.original_path} because of unsupported audio track language: '{subtitle.audio_language}'")
                subtitle.content = None
                return
        
        logger.info(f'WhisperAI Starting {subtitle.task} to {wlm.get_name(output_language)} for {subtitle.video.original_path}')
        startTime = time.time()
        video_name = subtitle.video.original_path if self.pass_video_name else None

        r = self.session.post(f"{self.endpoint}/asr",
                              params={'task': subtitle.task, 'language': input_language, 'output': 'srt', 'encode': 'false',
                                      'video_file': video_name},
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

        logger.info(f'WhisperAI Completed {subtitle.task} to {wlm.get_name(output_language)} in {elapsedTime} for {subtitle.video.original_path}')

        subtitle.content = r.content
