from fastapi import APIRouter, UploadFile, File, HTTPException, Depends,Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi_limiter.depends import RateLimiter
from ocr.utils import embed_and_upsert_page,create_query_embedding
from fastapi_limiter.depends import RateLimiter
from caching.cache import get_cache_key
import json,asyncio
from aiocache import caches


ocr_router = APIRouter()

# Dependency to get the Pinecone index
def get_pinecone_index(request: Request):
    return request.app.state.pinecone_index


# Dependency to get the Pinecone index
def get_caches_obj(request: Request):
    return request.app.state.caches

@ocr_router.post("/processOCR", dependencies=[Depends(RateLimiter(times=1, seconds=180))])
async def process_ocr_document(request:Request,file: UploadFile = File(...),pinecone_index=Depends(get_pinecone_index)):
    try:
        content = await file.read()
        ocr_data = json.loads(content)
        pages = ocr_data['analyzeResult']['pages'][:10]

        # Process embeddings asynchronously for all pages
        await asyncio.gather(*(embed_and_upsert_page(page,pinecone_index,request.app) for page in pages))

        return {"status": "OCR processing and embedding completed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ocr_router.post("/queryOCR/")
async def query_ocr_data(request:Request,query: str,pinecone_index=Depends(get_pinecone_index),caches=Depends(get_caches_obj)):
    try:
        # Create embedding for the query text
        query = query.strip().lower()
        query_embedding = await create_query_embedding(query,request.app)
        cache_key = await get_cache_key(query_embedding)
        # Attempt to fetch cached results
        # cached_results = await caches.get('default').get(cache_key)
        cached_results = await caches.get(cache_key)
        print(f"-------here------------------")
        if cached_results:
            return JSONResponse(cached_results)


        # Perform similarity search in Pinecone index
        # search_results = index.query(vector=query_embedding, top_k=10, include_metadata=True,include_values=True)
        search_results = pinecone_index.query(vector=query_embedding, top_k=10,include_metadata=True)

        # Prepare results to be cached
        results = []
        for match in search_results['matches']:
            page_number = match['metadata']['page_number']
            result = {
                'score': match['score'],
                'page_number': page_number,
            }
            results.append(result)

        # Cache the results
        # await caches.get('default').set(cache_key, results, ttl=60*5)  # Cache for 5 minutes
        await caches.set(cache_key, results, ttl=60*5)  # Cache for 5 minutes


        # Create a generator to yield results as they are processed
        async def result_generator():
            for match in search_results['matches']:
                page_number = match['metadata']['page_number']
                # content_embeddings = match['values']
                # content = match['metadata']['content']

                result = {
                    'score': match['score'],
                    'page_number': page_number,
                    # 'vector_values': content_embeddings,
                    # 'content': content
                }
                
                # Yield the result as a JSON string
                yield json.dumps(result, ensure_ascii=False).encode('utf-8') + b"\n"

        # Stream the response
        return StreamingResponse(result_generator(), media_type="application/json")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))