import logging

from bazarr.app.logger import UnwantedWaitressMessageFilter

def test_true_for_bazarr():
  record = logging.makeLogRecord({
    "level": logging.INFO,
    "msg": "a message from BAZARR for logging"
  })
  assert UnwantedWaitressMessageFilter().filter(record)

def test_false_below_error():
  record = logging.makeLogRecord({
    "level": logging.INFO
  })
  assert not UnwantedWaitressMessageFilter().filter(record)

def test_true_error_up():
  record = logging.makeLogRecord({
    "level": logging.CRITICAL
  })
  assert UnwantedWaitressMessageFilter().filter(record)
