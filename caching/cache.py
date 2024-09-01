import hashlib
from aiocache import caches
import numpy as np
import redis
from fastapi_limiter import FastAPILimiter
from fastapi import FastAPI

def init_cache(app: FastAPI):
    caches.set_config({
         'default': {
            'cache': "aiocache.RedisCache",
             'endpoint':app.state.redis_host,
             'port': app.state.redis_port,
             'timeout': 10,
             'serializer': {
                 'class': "aiocache.serializers.JsonSerializer"
             }
         }
    })
    app.state.caches = caches.get('default')


async def get_cache_key(query_embedding):
    embedding_str = np.array(query_embedding).tobytes()
    cache_key = hashlib.md5(embedding_str).hexdigest()
    return cache_key
