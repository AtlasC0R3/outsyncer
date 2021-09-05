# Outsyncer
A CLI-based app meant to synchronize songs from one device to another, *but can also be used to sort song files elegantly*

**THIS PROJECT IS NOT FINISHED YET!** If you use it *now*, be ready to figure out how this thing works by yourself.
Please look at the [GitHub Projects](https://github.com/users/AtlasC0R3/projects/2) page for this project.

spoiler alert: if you don't like swear words, don't go through the code.
<!-- fucking told you. -->

## What can it do?
- **synchronize music files from one device to another** through KDE Connect (Linux only)
- convert files before synchronizing *using [FFmpeg](https://ffmpeg.org/)*
- customize how files are organized *(custom formats, not quite "reliable")*
- **reorganize music files and directories** to a specific directory using custom formats
- exclude specific tracks, albums or artists from being sorted/synchronized

## F.A.Q.
### Can I save configurations instead of manually having to enter arguments?
No, **but you can write shell files** to hopefully solve this problem. For example:

outsyncer.sh
```shell
#!/usr/bin/env bash
python3 -m outsyncer --log debug --path "PATH" --force-ffmpeg --custom-format "{t.artist}||({t.year}) {t.album}||{t.tracknumber} {t.title}" --folderformat
```
outsyncer.bat
```shell
py -m outsyncer --log debug --path "PATH" --force-ffmpeg --custom-format "{t.artist}||({t.year}) {t.album}||{t.tracknumber} {t.title}" --folderformat
```

### What is KDE Connect? Why can't I use it on Windows?
Okay, first off, **I DIDN'T MAKE OR HAVE ANY RELATION WITH KDE OR KDE CONNECT**.
KDE Connect is a program that "connects everything to everything", that is cross-platform.
However, making the KDE Connect connectivity work on Windows isn't very possible; 
KDE Connect on Linux mounts a directory that essentially is just a portal for apps and file managers 
to access a KDE Connect device. This doesn't happen under Windows due to how Windows works.

### Will there be MTP support?
Unfortunately, *no*. I couldn't find any modern Python MTP libraries that worked.

*Copyright (C) 2021 atlas_core*