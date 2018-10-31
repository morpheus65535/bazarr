import os
import sys
import getopt

config_dir = os.path.join(os.path.dirname(__file__), '../data/')
no_update = False
console_debug = False
arguments = []


try:
    opts, args = getopt.getopt(sys.argv[1:],"h:",["no-update", "config=", "debug"])
except getopt.GetoptError:
    print 'bazarr.py -h --no-update --config <config_directory>'
    sys.exit(2)

for opt, arg in opts:
    arguments.append(opt)
    if arg != '':
        arguments.append(arg)
    if opt == '-h':
        print 'bazarr.py -h --no-update --config <config_directory>'
        sys.exit()
    elif opt in "--no-update":
        no_update = True
    elif opt in "--config":
        config_dir = arg
    elif opt in "--debug":
        console_debug = True
