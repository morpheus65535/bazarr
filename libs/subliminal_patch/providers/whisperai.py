from __future__ import absolute_import
import logging

from requests import Session

from subliminal_patch.subtitle import Subtitle
from subliminal_patch.providers import Provider
from subliminal import __short_version__
from subliminal.exceptions import ConfigurationError
from subzero.language import Language
from subliminal.video import Episode, Movie

import ffmpeg


logger = logging.getLogger(__name__)


class WhisperAISubtitle(Subtitle):
    '''Whisper AI Subtitle.'''
    provider_name = 'whisperai'
    hash_verifiable = False

    def __init__(self, language, video):
        super(WhisperAISubtitle, self).__init__(language)

        self.video = video

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

    # These are all the languages Whisper supports.
    # from whisper.tokenizer import LANGUAGES
    whisper_languages = ['eng', 'chi', 'ger', 'spa', 'rus', 'kor', 'fre', 'jpn', 'por', 'tur', 'pol', 'cat', 'dut', 'ara', 'swe', 'ita', 'ind', 'hin', 'fin', 'vie', 'heb', 'ukr', 'gre', 'may', 'cze', 'rum', 'dan', 'hun', 'tam', 'nor', 'tha', 'urd', 'hrv', 'bul', 'lit', 'lat', 'mao', 'mal', 'wel', 'slo', 'tel', 'per', 'lav', 'ben', 'srp', 'aze', 'slv', 'kan', 'est', 'mac', 'bre', 'baq', 'ice', 'arm', 'nep', 'mon', 'bos', 'kaz', 'alb', 'swa', 'glg', 'mar', 'pan', 'sin', 'khm', 'sna', 'yor', 'som', 'afr', 'oci', 'geo', 'bel', 'tgk', 'snd', 'guj', 'amh', 'yid', 'lao', 'uzb', 'fao', 'hat', 'pus', 'tuk', 'nno', 'mlt', 'san', 'ltz', 'bur', 'tib', 'tgl', 'mlg', 'asm', 'tat', 'haw', 'lin', 'hau', 'bak', 'jav', 'sun']

    languages = {
        Language.fromalpha3b(lang) for lang in whisper_languages
    }
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

    def query(self, language, video):
        return WhisperAISubtitle(language, video)

    def list_subtitles(self, video, languages):
        subtitles = [self.query(l, video) for l in languages]
        return [s for s in subtitles if s is not None]

    def download_subtitle(self, subtitle: WhisperAISubtitle):
        # Invoke Whisper through the API. This may take a long time depending on the file.
        # TODO: This loads the entire file into memory, find a good way to stream the file in chunks

        logger.debug("Encoding audio stream to WAV with ffmpeg")

        try:
            # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
            # Requires the ffmpeg CLI and `ffmpeg-python` package to be installed.
            out, _ = (
                ffmpeg.input(subtitle.video.original_path, threads=0)
                .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=16000)
                .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

        logger.debug(f"Finished encoding audio stream in {subtitle.video.original_path} with no errors")

        r = self.session.post(f"{self.endpoint}/asr",
                              params={'task': 'transcribe', 'language': subtitle.language, 'output': 'srt', 'encode': 'false'},
                              files={'audio_file': out},
                              timeout=self.timeout)

        subtitle.content = r.content
