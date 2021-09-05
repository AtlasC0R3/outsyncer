class Track:
    def __init__(self, tags, filename):
        self.tags = tags

        self.file_ext = filename.split('.')[-1]
        self.title = tags['tracktitle'].first
        self.artist = tags['albumartist'].first
        self.album = tags['album'].first
        self.artwork = tags['artwork'].first
        self.comment = tags['comment'].first
        self.discnumber = tags['discnumber'].first
        self.genre = tags['genre'].first
        self.year = tags['year'].first
        self.tracknumber = tags['tracknumber'].first

        self.filename = filename
        # This is ugly.
