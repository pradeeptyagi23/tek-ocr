from fastapi import HTTPException


async def embed_and_upsert_page(page, index, app):
    """
    Embeds the content of a single page and upserts the embedding into the Pinecone index.

    Args:
        page (dict): The page object containing content and metadata.
        index: The Pinecone index object where embeddings are upserted.
        app: The FastAPI application object for accessing external services.

    Raises:
        HTTPException: If an error occurs during embedding or upserting.
    """
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
            'content': page_content
        }

        index.upsert(vectors=[(f"{page['pageNumber']}", page_embedding, metadata)])

    except Exception as e:
        print(f"Error processing page {page['pageNumber']}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing page {page['pageNumber']}: {str(e)}")


async def create_query_embedding(query_text: str, app):
    """
    Creates an embedding for the provided query text.

    Args:
        query_text (str): The text to create an embedding for.
        app: The FastAPI application object for accessing external services.

    Returns:
        list: The embedding vector for the query text.

    Raises:
        HTTPException: If an error occurs during embedding creation.
    """
    try:
        response = await app.state.aclient.embeddings.create(
            input=query_text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create query embedding: {str(e)}")
