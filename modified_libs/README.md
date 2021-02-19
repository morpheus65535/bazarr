# bazarr modified or self-written libs

This directory holds external dependencies that are
either built by the bazarr project, moved from other
projects to bazarr, or taken from upstream and modified
without having contributed back the changes, or simply libraries
that are not available in the state bazarr wants/needs them.

This file tries to keep track of those.
Tracking is a manual process, so it is possible this file is not
complete or up-to-date.

## Developed by or moved to bazarr

subliminal_patch
subzero
libfilebot

### subliminal_patch

Originally developed in the plex Subzero plugin
(Add attribution here to original author etc)

(Add description of what it is etc)

### subzero

(Add attribution here)

(Add description here)

### libfilebot

(Add attribution here)

(Add description here)

## Dependencies that cannot be tracked back to a normal version/commit

deathbycaptcha

### deathbycaptcha

(Add attribution here)
*POSSIBLY* from https://github.com/rejoiceinhope/python-deathbycaptcha

The bundled version is not succesful traced back to a git commit or published public version


## Modified without contributed back

subliminal
cloudscraper

### subliminal

(Add attribution here)

(Add description here)

### cloudscraper

https://github.com/VeNoMouS/cloudscraper
Copyright (c) 2019 VeNoMouS
Copyright (c) 2015 Anorov

The project started uploading releases to pypi starting
at version 1.1.13. The version tested with bazarr is 1.1.9
with some commits to upstream pulled in, and a locally fetched
browsers.json file.

It's basically:
1.1.9 - https://github.com/VeNoMouS/cloudscraper/commit/7bc0ee6f72458a2385184ff49b9b3930ba7592d6
patch for loading browsers.json:
https://github.com/VeNoMouS/cloudscraper/commit/84fcf9e049230b9b0106d74c4e8c96cbab7ca11e:

Installing 1.1.9 from git does not pull in the browsers.json.
Earliest packaged version is with 1.1.13, but this brings in a lot of
changes around reCaptcha handling that breaks the way it is used
by subliminal_patch now.
