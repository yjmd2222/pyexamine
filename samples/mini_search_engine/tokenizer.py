class Tokenizer:
    def split(self, text: str):
        return [t for t in text.replace(".", " ").split() if t]
