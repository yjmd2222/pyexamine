class Indexer:
    def build(self, tokens):
        return {token: idx for idx, token in enumerate(tokens)}
