class FakeAPI:
    def get(self, path, payload=None):
        return {"path": path, "payload": payload, "ok": True}
    def post(self, path, payload=None):
        return {"path": path, "payload": payload, "ok": True}
    def patch(self, path, payload=None):
        return {"path": path, "payload": payload, "ok": True}

def repetitive_sync(client, ids):
    out = []
    for ident in ids:
        out.append(client.get("/items", {"id": ident}))
        out.append(client.get("/items", {"id": ident}))
        out.append(client.get("/items", {"id": ident}))
        out.append(client.post("/items", {"id": ident}))
        out.append(client.post("/items", {"id": ident}))
    for ident in ids:
        client.get("/status", {"id": ident})
        client.get("/status", {"id": ident})
        client.get("/status", {"id": ident})
        client.patch("/status", {"id": ident, "x": 1})
    return out
