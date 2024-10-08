import os
from dotenv import load_dotenv
from fastapi import FastAPI
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from pinecone import Pinecone, ServerlessSpec
from openai import AsyncOpenAI
import boto3

load_dotenv()


def setup_env(app: FastAPI) -> None:
    """
    Set up environment variables and application state.

    Args:
        app (FastAPI): The FastAPI application instance.

    Reads environment variables and assigns them to the application state.
    """
    app.state.USER_POOL_ID = os.getenv("USER_POOL_ID")
    app.state.CLIENT_ID = os.getenv("CLIENT_ID")
    app.state.REGION = os.getenv("REGION")
    app.state.SECRET_KEY = os.getenv("SECRET_KEY")
    app.state.ALGORITHM = "HS256"

    app.state.redis_host = os.getenv("REDIS_HOST", "localhost")
    app.state.redis_port = int(os.getenv("REDIS_PORT", 6379))
    app.state.pinecone_page_count = int(os.getenv("PINECONE_PAGE_COUNT", 10))


def setup_cognito(app: FastAPI) -> None:
    """
    Set up AWS Cognito client.

    Args:
        app (FastAPI): The FastAPI application instance.

    Initializes the AWS Cognito client and assigns it to the application state.
    """
    app.state.cognito_client = boto3.client("cognito-idp", region_name=app.state.REGION)


def setup_pinecone(app: FastAPI) -> None:
    """
    Set up Pinecone client and index.

    Args:
        app (FastAPI): The FastAPI application instance.

    Initializes the Pinecone client and creates the index if it does not exist.
    """
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENV = os.getenv("PINECONE_ENV")
    pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV, pool_threads=10)
    pinecone_index_name = "tek-ocr-embeddings"

    if pinecone_index_name not in pc.list_indexes().names():
        pc.create_index(
            name=pinecone_index_name,
            dimension=1536,  # The dimension of the embeddings
            metric="dotproduct",  # Similarity metric
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    app.state.pinecone_index = pc.Index(pinecone_index_name)


def setup_aclient(app: FastAPI) -> None:
    """
    Set up OpenAI client.

    Args:
        app (FastAPI): The FastAPI application instance.

    Initializes the OpenAI client and assigns it to the application state.
    """
    app.state.aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def setup_redis_client(app: FastAPI) -> None:
    """
    Set up Redis client and initialize rate limiter.

    Args:
        app (FastAPI): The FastAPI application instance.

    Initializes the Redis client and configures FastAPILimiter.
    """
    app.state.redis_client = redis.Redis(
        host=app.state.redis_host,
        port=app.state.redis_port,
        db=0,
        decode_responses=True,
    )
    await FastAPILimiter.init(app.state.redis_client)
