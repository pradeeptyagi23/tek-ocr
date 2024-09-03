import json
import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi_limiter.depends import RateLimiter
from ocr.utils import embed_and_upsert_page, create_query_embedding
from auth.utils import get_current_user
from caching.cache import get_cache_key
from typing import Dict, Generator, Any
from pinecone import Index
from aiocache import Cache

ocr_router = APIRouter()


def get_pinecone_index(request: Request) -> Index:
    """
    Dependency to retrieve the Pinecone index from the application state.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        Pinecone index: The Pinecone index instance.
    """
    return request.app.state.pinecone_index


def get_caches_obj(request: Request) -> Cache:
    """
    Dependency to retrieve the cache object from the application state.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        aiocache.Cache: The cache object instance.
    """
    return request.app.state.caches


@ocr_router.post(
    "/processOCR", dependencies=[Depends(RateLimiter(times=1, seconds=180)),
                                 Depends(get_current_user)]
)
async def process_ocr_document(
    request: Request,
    file: UploadFile = File(...),
    pinecone_index: Index = Depends(get_pinecone_index),
) -> Dict[str, str]:
    """
    Process and embed OCR data from an uploaded file and
    upsert the embeddings into Pinecone.

    Args:
        request (Request): The FastAPI request object.
        file (UploadFile): The uploaded file containing OCR data.
        pinecone_index: Dependency to get the Pinecone index.

    Returns:
        dict: A status message indicating completion.

    Raises:
        HTTPException: If an error occurs during processing.
    """
    try:
        content = await file.read()
        ocr_data = json.loads(content)
        pages = ocr_data["analyzeResult"]["pages"][:10]

        # Process embeddings asynchronously for all pages
        await asyncio.gather(
            *(
                embed_and_upsert_page(page, pinecone_index, request.app)
                for page in pages
            )
        )

        return {"status": "OCR processing and embedding completed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ocr_router.post("/queryOCR/", response_model=None)
async def query_ocr_data(
    request: Request,
    query: str,
    pinecone_index: Index = Depends(get_pinecone_index),
    caches: Cache = Depends(get_caches_obj),
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    Query OCR data using the provided query text and return results from Pinecone index.

    Args:
        request (Request): The FastAPI request object.
        query (str): The query text for searching.
        pinecone_index: Dependency to get the Pinecone index.
        caches: Dependency to get the cache object.

    Returns:
        StreamingResponse: A streaming response of the search results in JSON format.

    Raises:
        HTTPException: If an error occurs during querying or caching.
    """
    try:
        query = query.strip().lower()
        query_embedding = await create_query_embedding(query, request.app)
        cache_key = await get_cache_key(query_embedding)

        # Attempt to fetch cached results
        cached_results = await caches.get(cache_key)
        if cached_results:
            return JSONResponse(cached_results)

        # Perform similarity search in Pinecone index
        search_results = pinecone_index.query(
            vector=query_embedding, top_k=10, include_metadata=True
        )

        # Prepare results to be cached
        results = [
            {"score": match["score"], "page_number": match["metadata"]["page_number"]}
            for match in search_results["matches"]
        ]

        # Cache the results
        await caches.set(cache_key, results, ttl=60 * 5)  # Cache for 5 minutes

        async def result_generator() -> Generator[bytes, None, None]:  # type: ignore
            """
            Generator to yield search results as JSON strings.


            Yields:
                bytes: A JSON-encoded result string for each match.
            """
            for match in search_results["matches"]:
                result = {
                    "score": match["score"],
                    "page_number": match["metadata"]["page_number"],
                }
                yield json.dumps(result, ensure_ascii=False).encode("utf-8") + b"\n"

        return StreamingResponse(result_generator(), media_type="application/json")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
