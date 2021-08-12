class Track:
    artist = ""
    title = ""
    album = ""
    filename = ""
    file_ext = ""

    def __init__(self, tags, filename):
        self.file_ext = filename.split('.')[-1]
        self.title = tags['tracktitle'].first
        self.artist = tags['albumartist'].first
        self.album = tags['album'].first

        self.filename = tags.filename
