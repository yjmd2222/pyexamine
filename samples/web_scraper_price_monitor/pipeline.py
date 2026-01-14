class MonitorPipeline:
    def __init__(self, client, parser, cache, limiter, policy):
        self.client = client
        self.parser = parser
        self.cache = cache
        self.limiter = limiter
        self.policy = policy

    def run(self, url: str):
        client = self.client
        parser = self.parser
        cache = self.cache
        limiter = self.limiter
        policy = self.policy

        if not limiter.allow(url):
            return None

        html = client.get(url)
        data = parser.parse(html)
        cache.store(url, data)
        policy.check(data)
        return data
