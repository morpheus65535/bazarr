# coding=utf-8

# only primitive types can be specified here
# for other derived values, use constants.py

# bazarr environment variable names
ENV_STOPFILE = 'STOPFILE'
ENV_RESTARTFILE = 'RESTARTFILE'
ENV_BAZARR_ROOT_DIR = 'BAZARR_ROOT'

# bazarr subdirectories
DIR_BACKUP = 'backup'
DIR_CACHE = 'cache'
DIR_CONFIG = 'config'
DIR_DB = 'db'
DIR_LOG = 'log'
DIR_RESTORE = 'restore'

# bazarr special files
FILE_LOG = 'bazarr.log'
FILE_RESTART = 'bazarr.restart'
FILE_STOP = 'bazarr.stop'

# bazarr exit codes
EXIT_NORMAL = 0
EXIT_INTERRUPT = -100
EXIT_VALIDATION_ERROR = -101
EXIT_CONFIG_CREATE_ERROR = -102
EXIT_PYTHON_UPGRADE_NEEDED = -103
EXIT_REQUIREMENTS_ERROR = -104
EXIT_PORT_ALREADY_IN_USE_ERROR = -105
