from fastapi import FastAPI
from auth.routes import auth_router
from ocr.routes import ocr_router
from files.routes import file_router
from core.config import setup_env, setup_cognito,setup_pinecone,setup_aclient,setup_redis_client
from caching.cache import init_cache
from contextlib import asynccontextmanager
import redis
from fastapi_limiter import FastAPILimiter
from aiocache import caches

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_env(app)
    setup_cognito(app)
    setup_pinecone(app)
    setup_aclient(app)
    await setup_redis_client(app)
    init_cache(app)
    yield 
    await app.state.redis_client.close()

app.router.lifespan_context = lifespan

app.include_router(auth_router, prefix="/auth")
app.include_router(ocr_router, prefix="/ocr")
app.include_router(file_router, prefix="/files")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
