class LayoutPicker:
    def select(self, mode: str):
        if mode == "timeline":
            return "timeline"
        elif mode == "grid":
            return "grid"
        elif mode == "mosaic":
            return "mosaic"
        elif mode == "map":
            return "map"
        elif mode == "story":
            return "story"
        elif mode == "album":
            return "album"
        elif mode == "highlight":
            return "highlight"
        elif mode == "favorites":
            return "favorites"
        elif mode == "trip":
            return "trip"
        elif mode == "year":
            return "year"
        else:
            return "default"
