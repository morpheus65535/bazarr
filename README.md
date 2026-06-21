<p align="center">
  <img src="frontend/public/images/logo128.png" alt="Bazarr logo" width="96">
</p>

<h1 align="center">Bazarr</h1>

<p align="center">
  A companion application to Sonarr and Radarr that manages and downloads subtitles based on your requirements.
</p>

<p align="center">
  <a href="https://github.com/morpheus65535/bazarr/issues">
    <img src="https://img.shields.io/github/issues/morpheus65535/bazarr.svg?style=flat-square" alt="GitHub issues"></a>
  <a href="https://github.com/morpheus65535/bazarr/stargazers">
    <img src="https://img.shields.io/github/stars/morpheus65535/bazarr.svg?style=flat-square" alt="GitHub stars"></a>
  <a href="https://hub.docker.com/r/linuxserver/bazarr/">
    <img src="https://img.shields.io/docker/pulls/linuxserver/bazarr.svg?style=flat-square" alt="Docker pulls - linuxserver"></a>
  <a href="https://hub.docker.com/r/hotio/bazarr/">
    <img src="https://img.shields.io/docker/pulls/hotio/bazarr.svg?style=flat-square" alt="Docker pulls - hotio"></a>
  <a href="https://discord.gg/MH2e2eb">
    <img src="https://img.shields.io/badge/discord-chat-MH2e2eb.svg?style=flat-square" alt="Discord"></a>
</p>

## About

Bazarr is a companion application to Sonarr and Radarr. It manages and downloads subtitles based on your requirements. You define your preferences by TV show or movie, and Bazarr takes care of everything for you.

Bazarr does not scan your disk to detect series and movies. It only manages the series and movies that are indexed in Sonarr and Radarr.

## Links

| Resource | Link |
| --- | --- |
| Documentation | [Wiki](https://wiki.bazarr.media) |
| Support | [Discord](https://discord.gg/MH2e2eb) |
| Bug reports | [GitHub Issues](https://github.com/morpheus65535/bazarr/issues) |
| Feature requests | [Feature Upvote](http://features.bazarr.media) |

## Support the project

At the request of some users, here is a way to show appreciation for the efforts made in the development of Bazarr:

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XHHRWXT9YB7WE&source=url)

## Major features

- Support for major platforms: Windows, Linux, macOS, Raspberry Pi, etc.
- Automatically add new series and episodes from Sonarr.
- Automatically add new movies from Radarr.
- Series- and movie-based subtitle language configuration.
- Scan your existing library for internal and external subtitles and download any missing ones.
- Keep a history of what was downloaded, from where, and when.
- Manual search to download subtitles on demand.
- Upgrade previously downloaded subtitles when a better one is found.
- Delete external subtitles from disk.
- Support for 184 subtitle languages, including forced/foreign subtitles depending on providers.
- A beautiful UI based on Sonarr.

## Supported subtitle providers

- Addic7ed
- AnimeKalesi
- Animetosho (requires AniDb HTTP API client described [here](https://wiki.anidb.net/HTTP_API_Definition))
- AnimeSub.info
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
- Pipocas.tv
- Podnapisi
- Prijevodi-Online
- RegieLive
- Sous-Titres.eu
- subf2m.co
- Subs.sab.bz
- Subs4Free
- Subs4Series
- Subsarr (self-hosted, requires [slimcdk/subsarr](https://github.com/slimcdk/subsarr))
- Subscene
- Subscenter
- SubsRo
- Subsunacs.net
- SubSynchro
- Subtis
- Subtitrari-noi.ro
- subtitri.id.lv
- Subtitulamos.tv
- SubX
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

![Bazarr](screenshot/bazarr-screenshot.png?raw=true "Bazarr")

## Acknowledgements

Thanks to the folks at OpenSubtitles for their logo, which inspired ours.

## License

- [GNU GPL v3](http://www.gnu.org/licenses/gpl.html)
- Copyright 2010-2026
