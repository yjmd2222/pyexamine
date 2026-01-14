class HtmlExtractor:
    def open(self, path: str):
        return f"html:{path}"

    def extract(self, payload: str):
        return payload.lower()


class JsonExtractor:
    def open(self, path: str):
        return f"json:{path}"

    def extract(self, payload: str):
        return payload.strip()


class TextExtractor:
    def open(self, path: str):
        return f"text:{path}"

    def extract(self, payload: str):
        return payload.replace(" ", "")
