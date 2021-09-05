import os
from utils.classes import Track


def format_directory_file(t: Track, use_icon=True):
    if os.name == 'nt':
        if use_icon:
            icon_string_thingy = "IconFile=favicon.ico\r\nIconIndex=0"
        else:
            icon_string_thingy = ""
        return f"""[.ShellClassInfo]
NoSharing=1
{icon_string_thingy}
InfoTip={t.album} by {t.artist}, released in {t.year}
[ViewState]
FolderType=Music
Mode=
Vid="""
    elif os.name == 'posix':  # TODO: fuck around more with .directory files
        return f"""
[Desktop Entry]
Icon=favicon.ico
"""


directory_file_names = {'nt': 'desktop.ini', 'posix': '.directory'}
