# coding=utf-8

import os
import argparse


def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return 0
    else:
        raise ValueError(f"invalid truth value {val!r}")


no_update = os.environ.get("NO_UPDATE", "false").strip() == "true"
no_cli = os.environ.get("NO_CLI", "false").strip() == "true"

parser = argparse.ArgumentParser()

parser.register('type', bool, strtobool)

config_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data'))
parser.add_argument('-c', '--config', default=config_dir, type=str, metavar="DIR",
                    dest="config_dir", help="Directory containing the configuration (default: %s)" % config_dir)
parser.add_argument('-p', '--port', type=int, metavar="PORT", dest="port",
                    help="Port number (default: 6767)")
if not no_update:
    parser.add_argument('--no-update', default=False, type=bool, const=True, metavar="BOOL", nargs="?",
                        help="Disable update functionality (default: False)")
parser.add_argument('--debug', default=False, type=bool, const=True, metavar="BOOL", nargs="?",
                    help="Enable console debugging (default: False)")
parser.add_argument('--release-update', default=False, type=bool, const=True, metavar="BOOL", nargs="?",
                    help="Enable file based updater (default: False)")
parser.add_argument('--dev', default=False, type=bool, const=True, metavar="BOOL", nargs="?",
                    help="Enable developer mode (default: False)")
parser.add_argument('--no-tasks', default=False, type=bool, const=True, metavar="BOOL", nargs="?",
                    help="Disable all tasks (default: False)")
parser.add_argument('--no-signalr', default=False, type=bool, const=True, metavar="BOOL", nargs="?",
                    help="Disable SignalR connections to Sonarr and/or Radarr (default: False)")
parser.add_argument('--create-db-revision', default=False, type=bool, const=True, metavar="BOOL", nargs="?",
                    help="Create a new database revision that will be used to migrate database")


if not no_cli:
    args = parser.parse_args()
    if no_update:
        args.no_update = True
else:
    args = parser.parse_args(["-c", config_dir, "--no-update"])
