import indexer
import tokenizer
import storage
import cache
import ranking
import queries


def build_registry():
    return {
        "indexer": indexer.Indexer(),
        "tokenizer": tokenizer.Tokenizer(),
        "storage": storage.Storage(),
        "cache": cache.Cache(),
        "ranking": ranking.Ranker(),
        "queries": queries.QueryStore(),
    }
