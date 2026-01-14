class FetchSession:
    def __init__(self):
        self.calls = []

    def get(self, url: str):
        self.calls.append(url)
        return {"url": url}

    def post(self, url: str, payload):
        self.calls.append(url)
        return {"url": url, "payload": payload}


def fetch_prices(session: FetchSession, base_url: str, product_ids):
    results = []
    for product_id in product_ids:
        results.append(session.get(f"{base_url}/p/{product_id}"))
    results.append(session.get(f"{base_url}/p/extra-1"))
    results.append(session.get(f"{base_url}/p/extra-2"))
    results.append(session.get(f"{base_url}/p/extra-3"))
    results.append(session.get(f"{base_url}/p/extra-4"))
    results.append(session.get(f"{base_url}/p/extra-5"))
    results.append(session.get(f"{base_url}/p/extra-6"))
    results.append(session.get(f"{base_url}/p/extra-7"))
    results.append(session.get(f"{base_url}/p/extra-8"))
    results.append(session.post(f"{base_url}/log", {"count": len(results)}))
    return results
