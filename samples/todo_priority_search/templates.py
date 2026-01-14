class BoardBase:
    def render(self):
        return "base"


class BoardSimple(BoardBase):
    def render(self):
        return "simple"

    def export(self):
        return "export_simple"


class BoardAdvanced(BoardBase):
    def render(self):
        return "advanced"

    def export(self):
        return "export_advanced"


class CardBase:
    def paint(self):
        return "base"


class CardSimple(CardBase):
    def paint(self):
        return "simple"

    def export(self):
        return "export_simple"


class CardAdvanced(CardBase):
    def paint(self):
        return "advanced"

    def export(self):
        return "export_advanced"
