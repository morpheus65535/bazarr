# coding=utf-8

"""
Standalone ffsubsync worker. Bazarr launches it as a separate process so the CPU-heavy synchronization doesn't hold
the main process GIL and starve the web server.

Protocol:
  stdin:  one JSON object {"args": [...ffsubsync cli args...], "log_level": int}
  stdout: JSON lines {"type": "progress", "processed": float, "total": float|None}
                     {"type": "result", "result": {...}}
                     {"type": "error", "message": str}
  stderr: JSON lines {"name": str, "levelno": int, "msg": str} for each log record

This module must not import anything from Bazarr's `app` package: those imports have side effects (config loading,
database connection...).
"""

import json
import logging
import os
import sys
import traceback

_bazarr_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_bazarr_dir, '..', 'custom_libs'))
sys.path.insert(0, os.path.join(_bazarr_dir, '..', 'libs'))
sys.path.insert(0, os.path.join(_bazarr_dir, '..'))

_stdout = sys.stdout


def _emit(message):
    _stdout.write(json.dumps(message) + '\n')
    _stdout.flush()


class _JsonStderrHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = record.getMessage()
            if record.exc_info:
                msg = f'{msg}\n{"".join(traceback.format_exception(*record.exc_info))}'
            sys.stderr.write(json.dumps({'name': record.name, 'levelno': record.levelno, 'msg': msg}) + '\n')
            sys.stderr.flush()
        except Exception:
            pass


def _on_progress(info):
    _emit({'type': 'progress', 'processed': info.processed_seconds, 'total': info.total_seconds})


def main():
    if hasattr(os, 'nice'):
        try:
            os.nice(10)
        except OSError:
            pass

    # ffsubsync or its dependencies may print to stdout; keep stdout reserved for the protocol
    sys.stdout = sys.stderr

    payload = json.loads(sys.stdin.read())
    log_level = int(payload.get('log_level', logging.INFO))

    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    root.addHandler(_JsonStderrHandler())
    root.setLevel(log_level)

    try:
        from ffsubsync.ffsubsync import run, make_parser

        # ffsubsync calls logging.basicConfig() at import time; make sure we're the only handler
        for handler in list(root.handlers):
            if not isinstance(handler, _JsonStderrHandler):
                root.removeHandler(handler)
        for name in ('ffsubsync.subtitle_parser', 'ffsubsync.speech_transformers', 'ffsubsync.ffsubsync',
                     'ffsubsync.aligners'):
            logging.getLogger(name).setLevel(log_level)

        args = make_parser().parse_args(args=payload['args'])
        result = run(args, progress_handler=_on_progress)
    except SystemExit as e:
        _emit({'type': 'error', 'message': f'ffsubsync arguments parsing failed (exit code {e.code})'})
        return 1
    except BaseException:
        _emit({'type': 'error', 'message': traceback.format_exc()})
        return 1

    _emit({'type': 'result', 'result': result})
    return 0


if __name__ == '__main__':
    sys.exit(main())
