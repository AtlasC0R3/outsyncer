VORBIS_COMMENTS_KEYS = {
    'artist': ['artist', 'albumartist'],
    'title': 'title',
    'album': 'album'
}

MP4_KEYS = {
    'artist': '\xa9ART',
    'title': '\xa9nam',
    'album': '\xa9alb'
}

FORMAT_KEYS = {

    # ID3 TAGS
    'mp3': {
        'artist': ['TPE2', 'TPE1'],
        'title': 'TIT2',
        'album': 'TALB'
    },

    'mp4': MP4_KEYS,
    'm4a': MP4_KEYS,

    'flac': VORBIS_COMMENTS_KEYS,
    'ogg': VORBIS_COMMENTS_KEYS,
    'oga': VORBIS_COMMENTS_KEYS,
    'opus': VORBIS_COMMENTS_KEYS,

    'wma': {
        'artist': 'Author',
        'title': 'Title',
        'album': 'WM/AlbumTitle'
    }
}


class Track:
    artist = ""
    title = ""
    album = ""
    filename = ""
    file_ext = ""

    def __init__(self, file):
        file_ext = file.filename.split('.')[-1]
        title = file[FORMAT_KEYS[file_ext]['title']]
        self.title = str(title[0] if isinstance(title, list) else title)

        artist_key = FORMAT_KEYS[file_ext]['artist']
        if type(artist_key) is str:
            artist = file[artist_key]
        else:
            artist = None
            for key in artist_key:
                try:
                    artist = file[key]
                except KeyError:
                    pass
        artist = artist[0] if isinstance(artist, list) else artist
        artist = str(artist)
        artist = artist.split('\x00')
        self.artist = str(artist[0] if isinstance(artist, list) else artist)

        album = file[FORMAT_KEYS[file_ext]['album']]
        self.album = str(album[0] if isinstance(album, list) else album)

        self.filename = file.filename
        self.file_ext = file_ext
