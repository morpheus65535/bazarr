# coding=utf-8

import base64
import json
import logging
import os
import re
import requests
import subprocess
import sys
import time

from shutil import which
from threading import Event, Thread

from radarr.history import history_log_movie
from sonarr.history import history_log
from subtitles.processing import ProcessSubtitlesResult
from languages.get_languages import language_from_alpha2
from utilities.path_mappings import path_mappings
from app.config import settings
from app.get_args import args
from app.jobs_queue import jobs_queue, JobCanceled
from subtitles.tools.subsyncer import SubSyncer

# a hung process would hold one of the concurrent sync slots forever
LAPSE_TIMEOUT = 3600
# what LAPSE_PROGRESS=1 prints on stderr, ex: "Listening to the audio 40%"
PROGRESS = re.compile(r'(.+) (\d+)%')


def check_lapse(url, path):
    # for the settings test button, RuntimeError says what went wrong
    if url:
        try:
            response = requests.get(f'{url.rstrip("/")}/api/version', timeout=10)
            response.raise_for_status()
            return response.json()['version']
        except (requests.RequestException, ValueError, KeyError, TypeError) as e:
            raise RuntimeError(f'Could not get the version from {url}: {e}')

    exe = which(path or 'lapse')
    if not exe:
        raise RuntimeError(f'LAPSE executable not found ({path or "lapse is not in PATH"})')
    try:
        return subprocess.run([exe, '--version'], capture_output=True, text=True, timeout=10,
                              check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(f'Could not run {exe} --version: {e}')


class LapseUnavailable(Exception):
    pass


class LapseSyncer(SubSyncer):
    def sync(self, video_path, srt_path, srt_lang, hi, forced, reference=None, sonarr_series_id=None,
             sonarr_episode_id=None, radarr_id=None, job_id=None, force_sync=False, **kwargs):
        url = settings.subsync.lapse_url.strip().rstrip('/')
        path = settings.subsync.lapse_path.strip()
        # which() also checks that the file can be run
        exe = which(path or 'lapse')
        root, extension = os.path.splitext(srt_path)
        srtout = f'{root}.synced{extension}'
        try:
            if not url and not exe:
                raise LapseUnavailable(f'executable not found: {path or "lapse is not in PATH"}')

            # video, or a subtitles file to sync against
            source = video_path
            stream = reference if reference and reference[:2] in ('a:', 's:') and reference[2:].isdigit() else None
            no_embedded = False
            if reference and not stream and reference != video_path and os.path.isfile(reference):
                source = reference
            elif not stream:
                force_audio = settings.subsync.force_audio and not force_sync
                if settings.subsync.use_original_language or (settings.subsync.auto_use_original_language and
                                                              not force_audio):
                    stream = self._audio_stream_for_original_language(sonarr_series_id=sonarr_series_id,
                                                                      sonarr_episode_id=sonarr_episode_id,
                                                                      radarr_id=radarr_id)
                no_embedded = bool(force_audio and not stream)
            kind, track = (stream[0], int(stream[2:])) if stream else (None, None)
            options = {'no_embedded': no_embedded or kind == 'a',
                       'audio_track': track if kind == 'a' else None,
                       'sub_track': track if kind == 's' else None}

            # lapse writes nothing when the subtitles are already in sync, don't pick up an old attempt
            if os.path.isfile(srtout):
                os.remove(srtout)
            if url:
                result = self._run_remote(url, source, video_path, srt_path, srtout, options, job_id)
            else:
                result = self._run_local(exe, source, srt_path, srtout, options, job_id)

            if result['verdict'] != 'solid' or not os.path.isfile(srtout):
                logging.warning(f'BAZARR LAPSE left these subtitles untouched ({result["verdict"]}: '
                                f'{result.get("why") or "nothing to change"}): {srt_path}')
                return
            os.replace(srtout, srt_path)
            self._log_history(result, video_path, srt_path, srt_lang, hi, forced, sonarr_series_id,
                              sonarr_episode_id, radarr_id)
        except LapseUnavailable as e:
            logging.warning(f'BAZARR LAPSE is not available ({e}), using ffsubsync instead')
            return super().sync(video_path=video_path, srt_path=srt_path, srt_lang=srt_lang, hi=hi, forced=forced,
                                reference=reference, sonarr_series_id=sonarr_series_id,
                                sonarr_episode_id=sonarr_episode_id, radarr_id=radarr_id, job_id=job_id,
                                force_sync=force_sync, **kwargs)
        except TimeoutError:
            logging.error(f'BAZARR LAPSE did not finish within {LAPSE_TIMEOUT} seconds, original subtitles left '
                          f'untouched: {srt_path}')
        except (OSError, RuntimeError, ValueError, requests.RequestException) as e:
            logging.error(f'BAZARR LAPSE failed for this subtitle file: {srt_path}. {e}')
        finally:
            if os.path.isfile(srtout):
                os.remove(srtout)

    def _run_local(self, exe, source, srt_path, srtout, options, job_id):
        command = [exe, source, srt_path, '--output', srtout, '--no-backup', '--no-sidecar', '--json']
        if options['no_embedded']:
            command.append('--no-embedded')
        if options['audio_track'] is not None:
            command += ['--audio-track', str(options['audio_track'])]
        if options['sub_track'] is not None:
            command += ['--sub-track', str(options['sub_track'])]
        logging.debug(f'BAZARR running LAPSE: {command}')

        returncode, stdout, stderr = self._run(command, job_id)
        try:
            result = json.loads(stdout.splitlines()[-1])
        except (IndexError, ValueError):
            result = None
        # 2 and 3 are lapse saying nothing or unsure, not a crash
        if returncode not in (0, 2, 3) or not result:
            raise RuntimeError(f'Exit code {returncode}. {stderr.strip()}')
        return result

    @staticmethod
    def _run_remote(url, source, video_path, srt_path, srtout, options, job_id):
        def encode(path):
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode()

        payload = {'video': video_path, 'subtitle': encode(srt_path), 'filename': os.path.basename(srt_path),
                   'reference': None, 'reference_filename': None, **options}
        if source != video_path:
            payload.update(video=None, reference=encode(source), reference_filename=os.path.basename(source))

        job = jobs_queue.get_job(job_id)
        cancel_event = job.cancel_event if job else Event()
        deadline = time.monotonic() + LAPSE_TIMEOUT
        try:
            # lapse sends an empty line every second while it works, so 30s of nothing means it is gone
            response = requests.post(f'{url}/api/sync', json=payload, stream=True, timeout=(10, 30))
        except requests.ConnectionError as e:
            raise LapseUnavailable(e)

        with response:
            if response.status_code == 404:
                raise RuntimeError('LAPSE could not find the video. Mount your media in the LAPSE container at the '
                                   'same path as in Bazarr.')
            if not response.ok:
                raise RuntimeError(f'LAPSE answered {response.status_code}: {response.text[:300]}')

            for line in response.iter_lines():
                if cancel_event.is_set():
                    raise JobCanceled
                if time.monotonic() > deadline:
                    raise TimeoutError
                if not line:
                    continue
                message = json.loads(line)
                if 'error' in message:
                    raise RuntimeError(message['error'])
                if 'progress' in message:
                    jobs_queue.update_job_progress(job_id=job_id, progress_value=message['progress'],
                                                   progress_max=100, progress_message=message['phase'])
                    continue
                if message['subtitle']:
                    with open(srtout, 'wb') as f:
                        f.write(base64.b64decode(message['subtitle']))
                return message['done']
        raise RuntimeError('The connection to LAPSE closed before it sent a result')

    @staticmethod
    def _run(command, job_id):
        popen_kwargs = {}
        if sys.platform == 'win32':
            popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS

        job = jobs_queue.get_job(job_id)
        cancel_event = job.cancel_event if job else Event()
        deadline = time.monotonic() + LAPSE_TIMEOUT
        errors = []
        # HOME isn't always writable (ex: linuxserver image), the Bazarr config folder is
        env = {'LAPSE_CACHE': os.path.join(args.config_dir, 'cache', 'lapse'), **os.environ, 'LAPSE_PROGRESS': '1'}
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8',
                              errors='replace', env=env, **popen_kwargs) as process:
            reader = Thread(target=LapseSyncer._read_stderr, args=(process.stderr, job_id, errors), daemon=True)
            reader.start()
            try:
                while process.poll() is None and not cancel_event.wait(timeout=0.5):
                    if time.monotonic() > deadline:
                        raise TimeoutError
                if cancel_event.is_set():
                    raise JobCanceled
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                reader.join(timeout=5)
            # stdout only gets the one json line, it can't fill the pipe while lapse runs
            return process.returncode, process.stdout.read(), '\n'.join(errors[-5:])

    @staticmethod
    def _read_stderr(stream, job_id, errors):
        for line in stream:
            line = line.strip()
            progress = PROGRESS.fullmatch(line)
            if progress:
                jobs_queue.update_job_progress(job_id=job_id, progress_value=int(progress[2]), progress_max=100,
                                               progress_message=progress[1])
            elif line:
                errors.append(line)

    @staticmethod
    def _log_history(result, video_path, srt_path, srt_lang, hi, forced, sonarr_series_id, sonarr_episode_id,
                     radarr_id):
        message = (f"{language_from_alpha2(srt_lang)} subtitles synchronization ended with an offset of "
                   f"{result['offset_ms'] / 1000} seconds and a framerate scale factor of {result['ratio']:.2f}.")
        if result['parts'] > 1:
            message += f" The subtitles were split in {result['parts']} parts."

        if sonarr_series_id:
            prr = path_mappings.path_replace_reverse
        else:
            prr = path_mappings.path_replace_reverse_movie

        result = ProcessSubtitlesResult(message=message,
                                        reversed_path=prr(video_path),
                                        downloaded_language_code2=srt_lang,
                                        downloaded_provider=None,
                                        score=None,
                                        forced=forced,
                                        subtitle_id=None,
                                        reversed_subtitles_path=prr(srt_path),
                                        hearing_impaired=hi)

        if sonarr_episode_id:
            history_log(action=5, sonarr_series_id=sonarr_series_id, sonarr_episode_id=sonarr_episode_id,
                        result=result)
        else:
            history_log_movie(action=5, radarr_id=radarr_id, result=result)
