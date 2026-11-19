import logging

from bazarr.app.logger import FileHandlerFormatter, UnwantedWaitressMessageFilter

def test_true_for_bazarr():
  record = logging.LogRecord("", logging.INFO, "", 0, "a message from BAZARR for logging", (), None)
  assert UnwantedWaitressMessageFilter().filter(record)

def test_false_below_error():
  record = logging.LogRecord("", logging.INFO, "", 0, "", (), None)
  assert not UnwantedWaitressMessageFilter().filter(record)

def test_true_above_error():
  record = logging.LogRecord("", logging.CRITICAL, "", 0, "", (), None)
  assert UnwantedWaitressMessageFilter().filter(record)


SECRET = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
MASKED = "a1b2" + "x" * 28


def _redact(message):
  record = logging.LogRecord("", logging.INFO, "", 0, message, (), None)
  return FileHandlerFormatter("%(message)s").format(record)


def test_masks_signalr_access_token():
  out = _redact(f"http://sonarr:8989/signalr/messages?access_token={SECRET}")
  assert SECRET not in out
  assert out == f"http://sonarr:8989/signalr/messages?access_token={MASKED}"


def test_masks_jellyfin_authorization_token():
  out = _redact(f'Device="Bazarr", Token="{SECRET}"')
  assert SECRET not in out
  assert out == f'Device="Bazarr", Token="{MASKED}"'


def test_masks_header_mapping_forms():
  for header in ("X-API-KEY", "X-Plex-Token"):
    out = _redact(f"{{'{header}': '{SECRET}', 'Accept': 'application/json'}}")
    assert SECRET not in out, header
    assert out == f"{{'{header}': '{MASKED}', 'Accept': 'application/json'}}"


def test_masks_query_string_spellings():
  for param in ("apikey", "api_key", "apiKey", "apikey%3D"):
    sep = "" if param.endswith("%3D") else "="
    out = _redact(f"http://radarr/api/v3/movie?{param}{sep}{SECRET}&pageSize=1")
    assert SECRET not in out, param
    assert out == f"http://radarr/api/v3/movie?{param}{sep}{MASKED}&pageSize=1", param


def test_keeps_only_the_first_four_characters():
  # Enough of the key survives to tell which one was in play, and no more.
  out = _redact(f"apikey={SECRET}")
  assert out == f"apikey={SECRET[:4]}{'x' * 28}"


def test_masks_key_in_a_logged_traceback():
  out = _redact(f"Max retries exceeded with url: /api/v3/rootfolder?apikey={SECRET} "
                "(Caused by NewConnectionError('Failed to establish a new connection'))")
  assert SECRET[4:8] not in out
  assert f"rootfolder?apikey={MASKED} (Caused by" in out


def test_masks_keys_containing_punctuation():
  assert _redact("apikey=subdl_Cq7-5IU_x.9") == "apikey=subd" + "x" * 13


def test_key_no_longer_than_the_mask_is_masked_entirely():
  # A key at or under the mask length has nothing to spare, so none of it may
  # survive - and every one masks to the same width, so its length is hidden too.
  for length in range(1, 9):
    key = "s3cr3tk3y"[:length]
    assert _redact(f"apikey={key}") == "apikey=xxxxxxxx", key


def test_key_shorter_than_sixteen_characters_keeps_nothing():
  # Four characters of a short key would be too large a share of it.
  for length in range(9, 16):
    key = "s3cr3tk3ys3cr3tk3y"[:length]
    assert _redact(f"apikey={key}") == "apikey=" + "x" * length, key
  assert _redact("apikey=s3cr3tk3ys3cr3tk") == "apikey=s3cr" + "x" * 12


def test_empty_value_is_left_alone():
  # There is no key here to mask, so do not invent one.
  assert _redact("apikey=") == "apikey="


def test_masking_is_idempotent():
  once = _redact(f"?access_token={SECRET}")
  assert _redact(once) == once


def test_leaves_non_secrets_alone():
  for message in ("Bad AntiCaptcha API key",
                  "settings.plex.apikey_encrypted = True",
                  "Invalid SubX API key"):
    assert _redact(message) == message
