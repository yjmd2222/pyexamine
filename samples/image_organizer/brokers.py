class ImportBroker:
    def __init__(self, reader, scanner):
        self.reader = reader
        self.scanner = scanner

    def read(self, path: str):
        return self.reader.read(path)

    def scan(self, path: str):
        return self.scanner.scan(path)

    def refresh(self, path: str):
        return self.reader.read(path)

    def rescan(self, path: str):
        return self.scanner.scan(path)
