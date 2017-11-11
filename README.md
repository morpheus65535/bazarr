# bazarr
Bazarr is a companion application to Sonarr. It manage and download subtitles based on your requirements. You defined your preferences by TV show and Bazarr take care of everything for you.

## Major Features Include:

* Support for major platforms: Windows, Linux, macOS, Raspberry Pi, etc.
* Automatically add new series and episodes from Sonarr
* Series based configuration for subtitles languages
* Scan your existing library for internal and external subtitles and download any missing
* Keep history of what was downloaded from where and when
* Manual search so you can download subtitles on demand
* Ability to delete external subtitles from disk
* Currently support 184 subtitles languages
* And a beautiful UI based on Sonarr

## Supported subtitles providers:
* addic7ed
* legendastv
* opensubtitles
* podnapisi
* shooter
* subscenter
* thesubdb
* tvsubtitles

## Screenshot

You can get more in the [screenshot](https://github.com/morpheus65535/bazarr/tree/master/screenshot) directory but it should look familiar:

![Series](/screenshot/series.png?raw=true "Series")

## Running from Source

bazarr require Python 2.7 and can be run from source. This will use *git* as updater, so make sure that is installed.

Windows:

* Install [GIT](http://git-scm.com/)
* Install [Python 2.7](http://www.python.org/download/releases/2.7.3/)
* Open up CMD and go to the folder you want to install bazarr. Something like Program Files.
* Run `git clone https://github.com/morpheus65535/bazarr.git`.
* Run `pip install -r requirements.txt` to install dependencies.
* You can now start bazarr via `bazarr.py` to start bazarr.
* Open your browser and go to `http://localhost:6767/`

OS X:

* Install [GIT](http://git-scm.com/)
* Open up `Terminal`
* Go to your App folder `cd /Applications`
* Run `git clone https://github.com/morpheus65535/bazarr.git`
* Run `pip install -r requirements.txt` to install dependencies.
* You can now start bazarr via `bazarr.py` to start bazarr.
* Open your browser and go to `http://localhost:6767/`

Linux:

* (Ubuntu / Debian) Install [GIT](http://git-scm.com/) with `apt-get install git-core`
* (Fedora / CentOS) Install [GIT](http://git-scm.com/) with `yum install git`
* 'cd' to the folder of your choosing.
* Run `git clone https://github.com/morpheus65535/bazarr.git`
* Run `pip install -r requirements.txt` to install dependencies.
* You can now start bazarr via `bazarr.py` to start bazarr.
* Open your browser and go to `http://localhost:6767/`

## Docker:
* You can use [this image](https://hub.docker.com/r/morpheus65535/bazarr) to quickly build your own isolated app container. Thanks to [Linux Server](https://github.com/linuxserver) for the base image. It's based on the Linux instructions above. For more info about Docker check out the [official website](https://www.docker.com).

## First run (important to read!!!):

### 1 - Go to "Settings" page.
### 2 - In "General" tab:
*	Configure Bazarr settings (listening ip and port, base url and log level).
*	Configure Path Mappings only if you need it. Typical use case: Sonarr access episode files trough local path (D:\episodes\file.mkv) but Bazarr access those same episode files trough a network shared (\\server\episodes\file.mkv). In this case, you would be configuring Path Substitutions like this: D:\episodes --> \\server\episodes. If you don't set this correctly, you'll get http error 500 later down the road.
*	Configure updates. Recommended values are "master" and automatic enabled.
### 3 - In "Sonarr" tab:
*	Configure Sonarr ip, port, base url, SSL and API key.
### 4 - In "Subliminal" tab:
*	Configure enabled providers and enabled languages. Enabled languages are those that you are going to be able to assign to a series later.
### 5 - Save those settings and restart Bazarr.

### 6 - On the "Series" page, click on "Update Series"
* You should now see all your series listed with a wrench icon on yellow background. Those are the series that need to be configured. Click on each one and select desired languages. You have to do this even if you don't want subtitles for a series. Just click on the wrench icon and then on "Save".
* When you've finished going trough all those series to configure desired languages, you have to "Update All Episodes" from the "Series" page. Don't be impatient, it will take about 1 minute by 1000 episodes Bazarr need to scan for existing internal and external subtitles. If Bazarr is accessing those episodes trough a network share, it's going to take much more longer than that. Keep in mind that Bazarr have to open each and every episode files to analyze the content.
* Once the scan is finished, you should be able to access episodes list for each series and see those missing subtitles on the wanted page.

### 10 - Have fun and keep in mind that providers may temporary refuse connection due to connection limit exceeded or problem on the provider web service.

### License

* [GNU GPL v3](http://www.gnu.org/licenses/gpl.html)
* Copyright 2010-2017
