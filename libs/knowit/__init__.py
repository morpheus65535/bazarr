"""Know your media files better."""
from importlib import metadata

__title__ = metadata.metadata(__package__)['name']
__version__ = metadata.version(__package__)
__short_version__ = '.'.join(__version__.split('.')[:2])
__author__ = metadata.metadata(__package__)['author']
__license__ = metadata.metadata(__package__)['license']
__url__ = 'https://github.com/ratoaq2/knowit'

del metadata

#: Video extensions
VIDEO_EXTENSIONS = ('.3g2', '.3gp', '.3gp2', '.3gpp', '.60d', '.ajp', '.asf', '.asx', '.avchd', '.avi', '.bik',
                    '.bix', '.box', '.cam', '.dat', '.divx', '.dmf', '.dv', '.dvr-ms', '.evo', '.flc', '.fli',
                    '.flic', '.flv', '.flx', '.gvi', '.gvp', '.h264', '.m1v', '.m2p', '.m2ts', '.m2v', '.m4e',
                    '.m4v', '.mjp', '.mjpeg', '.mjpg', '.mk3d', '.mkv', '.moov', '.mov', '.movhd', '.movie', '.movx',
                    '.mp4', '.mpe', '.mpeg', '.mpg', '.mpv', '.mpv2', '.mxf', '.nsv', '.nut', '.ogg', '.ogm', '.ogv',
                    '.omf', '.ps', '.qt', '.ram', '.rm', '.rmvb', '.swf', '.ts', '.vfw', '.vid', '.video', '.viv',
                    '.vivo', '.vob', '.vro', '.webm', '.wm', '.wmv', '.wmx', '.wrap', '.wvx', '.wx', '.x264', '.xvid')

from knowit.api import KnowitException, know
