import pip

try:
    pip.main(['install', '--user', 'gitpython'])
except SystemExit as e:
    pass

try:
    pip.main(['install', '--user', 'langdetect'])
except SystemExit as e:
    pass