import pip

try:
    pip.main(['install', '--user', 'gitpython'])
except SystemExit as e:
    pass