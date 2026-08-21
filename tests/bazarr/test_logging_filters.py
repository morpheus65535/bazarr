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


def _redact(message):
  record = logging.LogRecord("", logging.INFO, "", 0, message, (), None)
  return FileHandlerFormatter("%(message)s").format(record)


def test_redacts_signalr_access_token():
  out = _redact(f"http://sonarr:8989/signalr/messages?access_token={SECRET}")
  assert SECRET not in out
  assert out == "http://sonarr:8989/signalr/messages?access_token=(removed)"


def test_redacts_jellyfin_authorization_token():
  out = _redact(f'Device="Bazarr", Token="{SECRET}"')
  assert SECRET not in out
  assert out == 'Device="Bazarr", Token="(removed)"'


def test_redacts_header_mapping_forms():
  for header in ("X-API-KEY", "X-Plex-Token"):
    out = _redact(f"{{'{header}': '{SECRET}', 'Accept': 'application/json'}}")
    assert SECRET not in out, header
    assert out == f"{{'{header}': '(removed)', 'Accept': 'application/json'}}"


def test_redacts_query_string_spellings():
  for param in ("apikey", "api_key", "apiKey", "apikey%3D"):
    sep = "" if param.endswith("%3D") else "="
    out = _redact(f"http://radarr/api/v3/movie?{param}{sep}{SECRET}&pageSize=1")
    assert SECRET not in out, param


def test_redacts_keys_containing_punctuation():
  assert _redact("apikey=subdl_Cq7-5IU_x.9") == "apikey=(removed)"


def test_redaction_is_idempotent():
  once = _redact(f"?access_token={SECRET}")
  assert _redact(once) == once


def test_leaves_non_secrets_alone():
  for message in ("Bad AntiCaptcha API key",
                  "settings.plex.apikey_encrypted = True",
                  "Invalid SubX API key"):
    assert _redact(message) == message
