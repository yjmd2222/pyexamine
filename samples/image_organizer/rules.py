class RetentionPolicy:
    def __init__(self, keep_raw: bool, keep_edits: bool):
        self.keep_raw = keep_raw
        self.keep_edits = keep_edits
        self._cache_hint = "hot"

    def apply(self, album):
        if self.keep_raw:
            album.raw = True
        if self.keep_edits:
            album.edits = True
        return album
