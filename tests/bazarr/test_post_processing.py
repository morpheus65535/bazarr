# coding=utf-8

import logging
import os
from unittest import mock

import pytest

from utilities.post_processing import pp_replace
from subtitles.post_processing import postprocessing


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

_DUMMY_CMD = 'cmd {{episode}} {{subtitles}} {{directory}}'


def _replace(episode, subtitles='sub.srt'):
    return pp_replace(
        _DUMMY_CMD,
        episode, subtitles,
        'English', 'en', 'eng',
        'English', 'en', 'eng',
        100, '1', 'manual', 'user', 'unknown', 1, 1,
    )


def _make_mock_process():
    proc = mock.MagicMock()
    proc.communicate.return_value = ('output', '')
    return proc


# ──────────────────────────────────────────────────────────────────────────────
# pp_replace – backslash safety in re.sub replacement strings (issue #3413)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("episode,subtitles,expected_fragment", [
    # Linux path – no backslashes
    ('/home/user/Videos/show.mkv', '/home/user/Videos/show.en.srt',
     '"/home/user/Videos/show.mkv"'),
    # Windows local path – backslash separators must not cause re.PatternError
    (r'C:\Videos\show.mkv', r'C:\Videos\show.en.srt',
     r'"C:\Videos\show.mkv"'),
    # Windows UNC path – \\ prefix and backslash-letter sequences like \y
    (r'\\Server\y\show.mkv', r'\\Server\y\show.en.srt',
     r'"\\Server\y\show.mkv"'),
    # UNC path with different share letters
    (r'\\NAS\media\show.mkv', r'\\NAS\media\show.en.srt',
     r'"\\NAS\media\show.mkv"'),
])
def test_pp_replace_does_not_raise_and_substitutes(episode, subtitles, expected_fragment):
    # Must not raise re.PatternError: bad escape
    result = _replace(episode, subtitles)
    assert expected_fragment in result


def test_pp_replace_unc_subtitle_path_preserved():
    # The leading \\ of a UNC subtitle path must survive substitution intact
    result = _replace(r'\\Server\drive\show.mkv', r'\\Server\drive\show.en.srt')
    assert r'"\\Server\drive\show.en.srt"' in result


def test_pp_replace_unc_directory_placeholder():
    result = _replace(r'\\Server\y\show.mkv')
    expected_dir = os.path.dirname(r'\\Server\y\show.mkv')
    assert f'"{expected_dir}"' in result


def test_pp_replace_linux_directory_placeholder():
    result = _replace('/srv/media/show.mkv')
    assert '"/srv/media"' in result


def test_pp_replace_windows_local_directory_placeholder():
    result = _replace(r'C:\Videos\show.mkv')
    expected_dir = os.path.dirname(r'C:\Videos\show.mkv')
    assert f'"{expected_dir}"' in result


# ──────────────────────────────────────────────────────────────────────────────
# postprocessing – Windows vs Unix subprocess invocation (issue #3413)
# ──────────────────────────────────────────────────────────────────────────────

def test_postprocessing_windows_uses_shell_false():
    command = r'python3 C:\Scripts\process.py "\\Server\y\subtitle.srt"'
    with mock.patch('os.name', 'nt'), \
         mock.patch('ctypes.windll', create=True) as mock_windll, \
         mock.patch('subprocess.Popen', return_value=_make_mock_process()) as mock_popen:
        mock_windll.kernel32.GetConsoleOutputCP.return_value = 1252
        postprocessing(command, r'\\Server\y\show.mkv')

    _, kwargs = mock_popen.call_args
    assert kwargs['shell'] is False


def test_postprocessing_windows_passes_args_as_list():
    # shlex.split(posix=False) tokenises without treating backslashes as escapes:
    # drive letters and UNC paths survive intact and quotes are preserved, so the
    # full command reaches Popen as an unmangled argv list.
    command = r'python3 C:\Scripts\process.py "\\Server\y\subtitle.srt"'
    with mock.patch('os.name', 'nt'), \
         mock.patch('ctypes.windll', create=True) as mock_windll, \
         mock.patch('subprocess.Popen', return_value=_make_mock_process()) as mock_popen:
        mock_windll.kernel32.GetConsoleOutputCP.return_value = 1252
        postprocessing(command, r'\\Server\y\show.mkv')

    args, _ = mock_popen.call_args
    assert isinstance(args[0], list)
    assert args[0] == ['python3', r'C:\Scripts\process.py', r'"\\Server\y\subtitle.srt"']


def test_postprocessing_windows_unc_path_not_mangled():
    # \\Server\y must not be stripped to \Server\y (shlex POSIX regression)
    unc_command = r'python3 "\\Server\y\subtitle.srt"'
    with mock.patch('os.name', 'nt'), \
         mock.patch('ctypes.windll', create=True) as mock_windll, \
         mock.patch('subprocess.Popen', return_value=_make_mock_process()) as mock_popen:
        mock_windll.kernel32.GetConsoleOutputCP.return_value = 1252
        postprocessing(unc_command, r'\\Server\y\show.mkv')

    args, _ = mock_popen.call_args
    assert r'"\\Server\y\subtitle.srt"' in args[0]


def test_postprocessing_windows_local_path_not_mangled():
    # C:\Scripts\... must not become C:Scripts... (shlex POSIX backslash-escape regression)
    local_command = r'python3 C:\Scripts\process.py'
    with mock.patch('os.name', 'nt'), \
         mock.patch('ctypes.windll', create=True) as mock_windll, \
         mock.patch('subprocess.Popen', return_value=_make_mock_process()) as mock_popen:
        mock_windll.kernel32.GetConsoleOutputCP.return_value = 1252
        postprocessing(local_command, r'C:\Videos\show.mkv')

    args, _ = mock_popen.call_args
    assert r'C:\Scripts\process.py' in args[0]


def test_postprocessing_unix_uses_shell_false():
    command = 'python3 /usr/local/bin/process.py "/srv/media/subtitle.srt"'
    with mock.patch('os.name', 'posix'), \
         mock.patch('subprocess.Popen', return_value=_make_mock_process()) as mock_popen:
        postprocessing(command, '/srv/media/show.mkv')

    _, kwargs = mock_popen.call_args
    assert kwargs['shell'] is False


def test_postprocessing_unix_passes_args_as_list():
    command = 'python3 /usr/local/bin/process.py "/srv/media/subtitle.srt"'
    with mock.patch('os.name', 'posix'), \
         mock.patch('subprocess.Popen', return_value=_make_mock_process()) as mock_popen:
        postprocessing(command, '/srv/media/show.mkv')

    args, _ = mock_popen.call_args
    assert isinstance(args[0], list)
    assert args[0] == ['python3', '/usr/local/bin/process.py', '/srv/media/subtitle.srt']


def test_postprocessing_unix_quoted_path_with_spaces():
    # A quoted path containing spaces must be a single argv token after shlex.split
    command = 'python3 /usr/local/bin/process.py "/srv/my media/subtitle.srt"'
    with mock.patch('os.name', 'posix'), \
         mock.patch('subprocess.Popen', return_value=_make_mock_process()) as mock_popen:
        postprocessing(command, '/srv/my media/show.mkv')

    args, _ = mock_popen.call_args
    assert args[0] == ['python3', '/usr/local/bin/process.py', '/srv/my media/subtitle.srt']


# ──────────────────────────────────────────────────────────────────────────────
# CWE-78 – OS command injection via untrusted release_info metadata
# ──────────────────────────────────────────────────────────────────────────────
#
# release_info is provider-supplied metadata and must be treated as attacker
# controlled. These tests assert that shell metacharacters embedded in
# release_info can never reach an OS shell: pp_replace quotes the value and
# postprocessing runs with shell=False, so at worst the metacharacters end up as
# inert argv tokens rather than being interpreted as commands.

_INJECTION_PAYLOADS = [
    '; rm -rf /',
    '&& rm -rf /',
    '|| rm -rf /',
    '| cat /etc/passwd',
    '`rm -rf /`',
    '$(rm -rf /)',
    '; shutdown -h now',
    '\n rm -rf /',
    '> /etc/passwd',
    '& calc.exe',
    '"; rm -rf / #',
]


def _replace_release_info(release_info, command='cmd {{release_info}}'):
    return pp_replace(
        command,
        '/srv/media/show.mkv', '/srv/media/show.en.srt',
        'English', 'en', 'eng',
        'English', 'en', 'eng',
        100, '1', 'manual', 'user', release_info, 1, 1,
    )


@pytest.mark.parametrize("payload", _INJECTION_PAYLOADS)
def test_release_info_injection_never_uses_shell(payload):
    # shell=False is the guarantee that prevents CWE-78: no OS shell ever parses
    # the metacharacters coming from release_info.
    command = _replace_release_info(payload)
    with mock.patch('os.name', 'posix'), \
         mock.patch('subprocess.Popen', return_value=_make_mock_process()) as mock_popen:
        postprocessing(command, '/srv/media/show.mkv')

    if mock_popen.call_args is None:
        # A malformed command (e.g. a quote break-out) makes shlex.split raise and
        # postprocessing bails out — nothing is executed, which is equally safe.
        return
    args, kwargs = mock_popen.call_args
    assert kwargs['shell'] is False
    assert isinstance(args[0], list)
    # The executable is always the intended command, never something the
    # attacker-controlled release_info could smuggle into the first token.
    assert args[0][0] == 'cmd'


@pytest.mark.parametrize("payload", [
    '; rm -rf /',
    '&& rm -rf /',
    '| cat /etc/passwd',
    '`rm -rf /`',
    '$(rm -rf /)',
])
def test_release_info_metacharacters_stay_single_token(payload):
    # A payload with no embedded quote to break out of is wrapped in double
    # quotes by pp_replace and survives shlex.split as a single inert argv token.
    command = _replace_release_info(payload)
    with mock.patch('os.name', 'posix'), \
         mock.patch('subprocess.Popen', return_value=_make_mock_process()) as mock_popen:
        postprocessing(command, '/srv/media/show.mkv')

    args, _ = mock_popen.call_args
    assert args[0] == ['cmd', payload]


@pytest.mark.parametrize("payload", _INJECTION_PAYLOADS)
def test_release_info_injection_never_uses_shell_on_windows(payload):
    # The same guarantee must hold on Windows, where shlex splits with posix=False.
    command = _replace_release_info(payload)
    with mock.patch('os.name', 'nt'), \
         mock.patch('ctypes.windll', create=True) as mock_windll, \
         mock.patch('subprocess.Popen', return_value=_make_mock_process()) as mock_popen:
        mock_windll.kernel32.GetConsoleOutputCP.return_value = 1252
        postprocessing(command, r'C:\Videos\show.mkv')

    if mock_popen.call_args is None:
        return
    args, kwargs = mock_popen.call_args
    assert kwargs['shell'] is False
    assert isinstance(args[0], list)
    assert args[0][0] == 'cmd'


# Windows cmd.exe command separators / substitution. These would chain commands
# if the string ever hit a shell (shell=True or cmd /c "..."); with shell=False
# and shlex posix=False they must survive as a single, inert quoted argv token.
_WINDOWS_INJECTION_PAYLOADS = [
    '& calc.exe',
    '&& del /q C:\\Windows',
    '| whoami',
    '|| calc.exe',
    '& shutdown /s /t 0',
    '%SystemRoot%\\system32\\calc.exe',
    '^& calc',
]


@pytest.mark.parametrize("payload", _WINDOWS_INJECTION_PAYLOADS)
def test_release_info_windows_metacharacters_stay_single_token(payload):
    # pp_replace wraps the value in double quotes; shlex.split(posix=False) keeps
    # those quotes and yields the whole payload as one token, so the cmd.exe
    # metacharacters never become separate argv entries a shell could act on.
    command = _replace_release_info(payload)
    with mock.patch('os.name', 'nt'), \
         mock.patch('ctypes.windll', create=True) as mock_windll, \
         mock.patch('subprocess.Popen', return_value=_make_mock_process()) as mock_popen:
        mock_windll.kernel32.GetConsoleOutputCP.return_value = 1252
        postprocessing(command, r'C:\Videos\show.mkv')

    args, kwargs = mock_popen.call_args
    assert kwargs['shell'] is False
    assert args[0] == ['cmd', f'"{payload}"']


# ──────────────────────────────────────────────────────────────────────────────
# Exception logging – the whole subtitle file shouldn't be logged
# ──────────────────────────────────────────────────────────────────────────────
#
# repr() of a UnicodeDecodeError includes its `object` attribute, which for a
# failed subtitle decode is the entire file. 
# str(e) keeps the diagnosis (codec, byte, position) and
# drops the payload; exc_info=True puts the exception type back, since this call
# site uses logging.error and so has no traceback of its own.

_PAYLOAD_MARKER = 'SUBTITLE-FILE-CONTENTS'
_FAKE_SUBTITLE = (_PAYLOAD_MARKER + ' ').encode() * 2000


def _run_postprocessing_raising(exc, caplog):
    with mock.patch('os.name', 'posix'), \
         mock.patch('subprocess.Popen', side_effect=exc), \
         caplog.at_level(logging.ERROR):
        postprocessing('python3 /usr/local/bin/process.py', '/srv/media/show.mkv')
    assert caplog.records, 'expected postprocessing to log the failure'
    return caplog.records[-1]


def test_postprocessing_failure_does_not_log_subtitle_contents(caplog):
    decode_error = UnicodeDecodeError(
        'utf-8', _FAKE_SUBTITLE, 15348, 15349, 'invalid start byte')
    record = _run_postprocessing_raising(decode_error, caplog)

    message = record.getMessage()
    assert _PAYLOAD_MARKER not in message
    assert len(message) < 500


def test_postprocessing_failure_still_logs_the_diagnosis(caplog):
    decode_error = UnicodeDecodeError(
        'utf-8', _FAKE_SUBTITLE, 15348, 15349, 'invalid start byte')
    record = _run_postprocessing_raising(decode_error, caplog)

    message = record.getMessage()
    # Everything needed to identify the offending file and byte survives.
    assert '/srv/media/show.mkv' in message
    assert 'invalid start byte' in message
    assert 'position 15348' in message


def test_postprocessing_failure_records_the_exception_type(caplog):
    record = _run_postprocessing_raising(ValueError(), caplog)

    assert record.exc_info is not None
    assert record.exc_info[0] is ValueError


def test_postprocessing_failure_does_not_log_contents_via_traceback(caplog):
    decode_error = UnicodeDecodeError(
        'utf-8', _FAKE_SUBTITLE, 15348, 15349, 'invalid start byte')
    record = _run_postprocessing_raising(decode_error, caplog)

    formatted = logging.Formatter('%(message)s').format(record)
    assert _PAYLOAD_MARKER not in formatted
    assert 'UnicodeDecodeError' in formatted
