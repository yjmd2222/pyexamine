class AlbumCatalog:
    def __init__(self):
        self.cover_path = ""
        self.owner = ""
        self.created = ""
        self.updated = ""
        self.title = ""
        self.subtitle = ""
        self.theme = ""
        self.layout = ""
        self.count = 0
        self.size = 0
        self.version = 1

    def set_title(self, title: str):
        self.title = title

    def set_owner(self, owner: str):
        self.owner = owner

    def set_theme(self, theme: str):
        self.theme = theme

    def set_layout(self, layout: str):
        self.layout = layout

    def set_cover_path(self, cover_path: str):
        self.cover_path = cover_path

    def generate_preview(self):
        return f"{self.title}:{self.cover_path}"
