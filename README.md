# bazarr
Bazarr is a companion application to Sonarr. It manage and download subtitles based on your requirements. You defined your preferences by TV show and Bazarr take care of everything for you.

## Major Features Include:

* Support for major platforms: Windows, Linux, macOS, Raspberry Pi, etc.
* Automatically add new episodes from Sonarr
* Scan your existing library for internal and external subtitles and download any missing
* Manual search so you can download subtitles on demand
* Ability to delete external subtitles from disk
* And a beautiful UI based on Sonarr

## Running from Source

bazarr require Python 2.7 and can be run from source. This will use *git* as updater, so make sure that is installed.

Windows:

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

Docker:
* You can use [this image](https://hub.docker.com/r/morpheus65535/bazarr) to quickly build your own isolated app container. It's based on the Linux instructions above. For more info about Docker check out the [official website](https://www.docker.com).

### License

* [GNU GPL v3](http://www.gnu.org/licenses/gpl.html)
* Copyright 2010-2017
