from flask_caching import Cache

def init_cache(app):
    cache = Cache(app.server, config={
        "CACHE_TYPE": "SimpleCache",   # en memoria
        "CACHE_DEFAULT_TIMEOUT": 86400 # 24h
    })
    return cache
