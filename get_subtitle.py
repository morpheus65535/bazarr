import os
from babelfish import *
from subliminal import *
from pycountry import *

# configure the cache
region.configure('dogpile.cache.dbm', arguments={'filename': 'cachefile.dbm'})

def download_subtitle(path, language, hi, providers):
    video = scan_video(path)
    best_subtitles = download_best_subtitles([video], {Language(language)}, providers=providers, hearing_impaired=hi)
    try:
        best_subtitle = best_subtitles[video][0]
    
        result = save_subtitles(video, [best_subtitle])
        downloaded_provider = str(result[0]).strip('<>').split(' ')[0][:-8]
        downloaded_language = pycountry.languages.lookup(str(str(result[0]).strip('<>').split(' ')[2].strip('[]'))).name
        message = downloaded_language + " subtitles downloaded from " + downloaded_provider + "."

        return message
    except:
        return None
