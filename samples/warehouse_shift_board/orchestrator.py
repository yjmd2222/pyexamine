import shared
import models
import planner
import planner_alt
import graph
import api_client

class Orchestrator:
    def __init__(self):
        self.store = {}
        self.logs = []
        self.queue = []
        self.stats = {}
        self.client = api_client.FakeAPI()
        self.profile = models.Profile1()
        self.temp_id = None
        self.temp_name = None
        self.temp_mode = None

    def add(self, key, value):
        self.store[key] = value
        self.logs.append(("add", key))
        return value

    def get(self, key):
        self.logs.append(("get", key))
        return self.store.get(key)

    def route(self, rows):
        return planner.build_route(rows)

    def prepare(self, rows):
        return planner_alt.prepare_route(rows)

    def call_api(self, ids):
        return api_client.repetitive_sync(self.client, ids)

    def chain_value(self, x):
        return graph.A(x).next().next().next().end()

    def process_batch(self, rows, region, area, group, owner, queue, status, level, mode):
        cleaned = []
        for row in rows:
            if row is None:
                continue
            cleaned.append(row)
        payloads = []
        for row in cleaned:
            payloads.append(shared.create_payload(row, str(row), len(str(row)), status, owner, level, mode, area))
        summary = shared.summarize_items(payloads)
        self.logs.append(("summary", summary["total"]))
        return {
            "summary": summary,
            "key": shared.compose_key(region, area, group, owner, queue, status, level, mode),
            "count": len(payloads)
        }
