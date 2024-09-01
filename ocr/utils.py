# Embedding and upserting function for a single page
from fastapi import HTTPException


async def embed_and_upsert_page(page,index,app):
    try:
        # Combine words into a single page content string
        page_content = " ".join([word['content'] for word in page['words']])
        print(f"Processing page {page['pageNumber']}")
        # Create embeddings for the page content
        response = await app.state.aclient.embeddings.create(
            input=page_content,
            model="text-embedding-ada-002"
        )

        page_embedding = response.data[0].embedding

        # Upsert the embedding with metadata
        metadata = {
            'page_number': page['pageNumber'],
            'content':page_content
        }

        index.upsert(vectors=[(f"{page['pageNumber']}", page_embedding, metadata)])

    except Exception as e:
        print(f"Error processing page {page['pageNumber']}: {e}") 



# Embedding function
async def create_query_embedding(query_text: str,app):
    try:
        response = await app.state.aclient.embeddings.create(
            input=query_text,
            model="text-embedding-ada-002"
        )
        # print(response)
        return response.data[0].embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create query embedding: {str(e)}")