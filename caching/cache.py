import hashlib
from aiocache import caches
import numpy as np
import redis
from fastapi_limiter import FastAPILimiter
from fastapi import FastAPI

def init_cache(app: FastAPI) -> None:
    """
    Initialize the cache configuration for the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance.

    Sets the cache configuration using Redis and attaches it to the application state.
    """
    caches.set_config({
        'default': {
            'cache': "aiocache.RedisCache",
            'endpoint': app.state.redis_host,
            'port': app.state.redis_port,
            'timeout': 10,
            'serializer': {
                'class': "aiocache.serializers.JsonSerializer"
            }
        }
    })
    app.state.caches = caches.get('default')

async def get_cache_key(query_embedding: np.ndarray) -> str:
    """
    Generate a cache key from a query embedding.

    Args:
        query_embedding (np.ndarray): The query embedding as a NumPy array.

    Returns:
        str: The generated cache key as a hexadecimal string.
    """
    embedding_str = np.array(query_embedding).tobytes()
    cache_key = hashlib.md5(embedding_str).hexdigest()
    return cache_key
