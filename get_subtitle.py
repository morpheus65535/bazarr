import os
from babelfish import *
from subliminal import *

# configure the cache
region.configure('dogpile.cache.dbm', arguments={'filename': 'cachefile.dbm'})

def download_subtitle(path, language, hi, providers):
    video = scan_video(path)
    best_subtitles = download_best_subtitles([video], {Language(language)}, providers=providers, hearing_impaired=hi)
    best_subtitle = best_subtitles[video][0]
    
    return save_subtitles(video, [best_subtitle])

#download_subtitle('Z:\Series TV\Vikings\Season 03\Vikings.S03E03.720p.HDTV.x264-KILLERS.mkv', 'fra', False, None)
