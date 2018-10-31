# libfilebot

Returns the `net.filebot.filename` property of a file without binary python package dependencies.
It instead uses system-provided binaries while *trying* to avoid calling the filebot-jvm-monstrosity.

*This is a quick-hack-excerpt from [Sub-Zero.bundle](https://github.com/pannal/Sub-Zero.bundle), so don't expect constant maintenance or code-quality.*

#### Currently supports:

* `xattr` command on darwin/osx
* NTFS advanced data streams via python pyADS
* `getfattr`, `attr` and `filebot` commands for every other OS


#### Dependencies

* [pyADS](https://github.com/RobinDavid/pyADS) for Windows