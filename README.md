# bazarr

Bazarr is a companion application to Sonarr and Radarr. It manages and downloads subtitles based on your requirements. You define your preferences by TV show or movie and Bazarr takes care of everything for you.

Be aware that Bazarr doesn't scan disk to detect series and movies: It only takes care of the series and movies that are indexed in Sonarr and Radarr.

Thanks to the folks at OpenSubtitles for their logo that was an inspiration for ours.

## Support on Paypal

At the request of some, here is a way to demonstrate your appreciation for the efforts made in the development of Bazarr:
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XHHRWXT9YB7WE&source=url)

# Status

[![GitHub issues](https://img.shields.io/github/issues/morpheus65535/bazarr.svg?style=flat-square)](https://github.com/morpheus65535/bazarr/issues)
[![GitHub stars](https://img.shields.io/github/stars/morpheus65535/bazarr.svg?style=flat-square)](https://github.com/morpheus65535/bazarr/stargazers)
[![Docker Pulls](https://img.shields.io/docker/pulls/linuxserver/bazarr.svg?style=flat-square)](https://hub.docker.com/r/linuxserver/bazarr/)
[![Docker Pulls](https://img.shields.io/docker/pulls/hotio/bazarr.svg?style=flat-square)](https://hub.docker.com/r/hotio/bazarr/)
[![Discord](https://img.shields.io/badge/discord-chat-MH2e2eb.svg?style=flat-square)](https://discord.gg/MH2e2eb)

# Support

For installation and configuration instructions, see [wiki](https://wiki.bazarr.media).

You can reach us for support on [Discord](https://discord.gg/MH2e2eb).

If you find a bug, please open an issue on [Github](https://github.com/morpheus65535/bazarr/issues).

# Feature Requests

If you need something that is not already part of Bazarr, feel free to create a feature request on [Feature Upvote](http://features.bazarr.media).

## Major Features Include:

- Support for major platforms: Windows, Linux, macOS, Raspberry Pi, etc.
- Automatically add new series and episodes from Sonarr
- Automatically add new movies from Radarr
- Series or movies based configuration for subtitles languages
- Scan your existing library for internal and external subtitles and download any missing
- Keep history of what was downloaded from where and when
- Manual search so you can download subtitles on demand
- Upgrade subtitles previously downloaded when a better one is found
- Ability to delete external subtitles from disk
- Currently support 184 subtitles languages with support for forced/foreign subtitles (depending of providers)
- And a beautiful UI based on Sonarr

## Supported subtitles providers:

- Addic7ed
- AnimeKalesi
- Animetosho (requires AniDb HTTP API client described [here](https://wiki.anidb.net/HTTP_API_Definition))
- Assrt
- AvistaZ, CinemaZ (Get session cookies using method described [here](https://github.com/morpheus65535/bazarr/pull/2375#issuecomment-2057010996))
- BetaSeries
- BSplayer
- Embedded Subtitles
- Gestdown.info
- GreekSubs
- GreekSubtitles
- HDBits.org
- Hosszupuska
- Karagarga.in
- Ktuvit (Get `hashed_password` using method described [here](https://github.com/XBMCil/service.subtitles.ktuvit))
- LegendasDivx
- Legendas.net
- Napiprojekt
- Napisy24
- Nekur
- OpenSubtitles.com
- OpenSubtitles.org (VIP users only)
- Podnapisi
- RegieLive
- Sous-Titres.eu
- Subdivx
- subf2m.co
- Subs.sab.bz
- Subs4Free
- Subs4Series
- Subscene
- Subscenter
- SubsRo
- Subsunacs.net
- SubSynchro
- Subtitrari-noi.ro
- subtitri.id.lv
- Subtitulamos.tv
- Supersubtitles
- Titlovi
- Titrari.ro
- Titulky.com
- Turkcealtyazi.org
- TuSubtitulo
- TVSubtitles
- Whisper (requires [ahmetoner/whisper-asr-webservice](https://github.com/ahmetoner/whisper-asr-webservice))
- Wizdom
- XSubs
- Yavka.net
- YIFY Subtitles
- Zimuku

## Screenshot

![Bazarr](/screenshot/bazarr-screenshot.png?raw=true "Bazarr")

### License

- [GNU GPL v3](http://www.gnu.org/licenses/gpl.html)
- Copyright 2010-2024
