from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
import aioboto3
import boto3
from pinecone import Pinecone,ServerlessSpec
import hashlib
from openai import AsyncOpenAI
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from fastapi.responses import StreamingResponse
from typing import List
import os,json

import asyncio

load_dotenv()

aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# AWS Cognito Configuration
USER_POOL_ID = os.getenv('USER_POOL_ID')
CLIENT_ID = os.getenv('CLIENT_ID')
REGION = os.getenv('REGION')



SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
cognito_client = boto3.client('cognito-idp', region_name=REGION)
# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Load your environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI

# Initialize Pinecone client
pc = Pinecone(
    api_key=os.environ.get("PINECONE_API_KEY"),
    environment=os.environ.get("PINECONE_ENV"),
    pool_threads=10
)

index_name = "tek-ocr-embeddings"

# Create the index if it doesn't exist
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # The dimension of the embeddings
        metric='cosine',  # Similarity metric
        spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    ) 
    )

# Connect to the index
index = pc.Index(index_name)

# Pydantic Models for User Registration and Confirmation
class UserRegistration(BaseModel):
    username: str
    password: str
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserConfirmation(BaseModel):
    username: str
    confirmation_code: str

#Ocr related
# Pydantic model for OCR data
class OCRWord(BaseModel):
    content: str

class OCRPage(BaseModel):
    pageNumber: int
    words: List[OCRWord]

class OCRDocument(BaseModel):
    pages: List[OCRPage]


# AWS S3 Configuration
bucket_name = "tek-file-bucket"

class FileLocations(BaseModel):
    file_paths:List[str]

# Embedding function
async def create_query_embedding(query_text: str):
    try:
        response = await aclient.embeddings.create(
            input=query_text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create query embedding: {str(e)}")

# Example function to retrieve content by embedding ID
def get_content_by_embedding_id(embedding_id: str) -> str:
    # Implement this function based on how you store your OCR content
    # This could involve a lookup in a database, file storage, etc.
    # For example:
    return "This is the full content associated with embedding ID " + embedding_id

# Embedding and upserting function for a single page
async def embed_and_upsert_page(page):
    try:
        # Combine words into a single page content string
        page_content = " ".join([word['content'] for word in page['words']])
        print(f"Processing page {page['pageNumber']}")
        # Create embeddings for the page content
        response = await aclient.embeddings.create(
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



def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    if expires_delta:
        to_encode.update({"exp": expires_delta})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username


async def file_exists(s3_client,file_key:str)->bool:
    try:

        await s3_client.head_object(Bucket=bucket_name,Key=file_key)
        return True
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            print(f"Got error {e.response}")
            raise HTTPException(status_code=500,detail='Error checking file existence')

async def upload_file_async(file_path:str,s3_client):
    try:
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=400,detail=f"File not found : {file_path}")

        print(f"Got file path {file_path}")
        with open(file_path,'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        file_key = f"{file_hash}/{os.path.basename(file_path)}"

        if await file_exists(s3_client,file_key):
            return f"File already exists : {file_key}"

        await s3_client.upload_file(file_path,bucket_name,file_key)

        signed_url = await s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket':bucket_name,'Key':file_key},
            ExpiresIn=3600
        )
        return signed_url

    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Failed to upload {file_path} : {str(e)}")


@app.post("/register/")
async def register_user(user: UserRegistration):
    try:
        response = cognito_client.sign_up(
            ClientId=CLIENT_ID,
            Username=user.username,
            Password=user.password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': user.email
                },
            ],
        )
        return {"message": "User registered successfully", "user_sub": response['UserSub']}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        response = cognito_client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': form_data.username,
                'PASSWORD': form_data.password,
            }
        )
        access_token = response['AuthenticationResult']['AccessToken']
        token_data = {"sub": form_data.username}
        jwt_token = create_access_token(token_data)
        return {"access_token": jwt_token, "token_type": "bearer"}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=f"Incorrect username or password {e}")


@app.post("/confirm/")
async def confirm_user(user: UserConfirmation):
    try:
        response = cognito_client.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=user.username,
            ConfirmationCode=user.confirmation_code,
        )
        return {"message": "User confirmed successfully"}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])


@app.post('/upload-files/')
async def upload_files(file_locations:FileLocations, current_user: str = Depends(get_current_user)):
    signed_urls = []
    file_ids = []

    session = aioboto3.Session(region_name=os.getenv("AWS_REGION"))
    async with session.client('s3') as s3_client:
        upload_tasks = [upload_file_async(file_path,s3_client) for file_path in file_locations.file_paths]

        signed_urls = await asyncio.gather(*upload_tasks)

    return {"signed_urls":signed_urls}


@app.post("/upload_ocr/")
async def process_ocr_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        ocr_data = json.loads(content)

        pages = ocr_data['analyzeResult']['pages'][:10]

        # Process embeddings asynchronously for all pages
        await asyncio.gather(*(embed_and_upsert_page(page) for page in pages))

        return {"status": "OCR processing and embedding completed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/")
async def query_ocr_data(query: str):
    try:
        # Create embedding for the query text
        query_embedding = await create_query_embedding(query)

        # Perform similarity search in Pinecone index
        search_results = index.query(vector=query_embedding, top_k=10, include_metadata=True,include_values=True)

        # Create a generator to yield results as they are processed
        async def result_generator():
            for match in search_results['matches']:
                page_number = match['metadata']['page_number']
                content_embeddings = match['values']
                content = match['metadata']['content']

                result = {
                    'score': match['score'],
                    'page_number': page_number,
                    'vector_values': content_embeddings,
                    'content': content
                }
                
                # Yield the result as a JSON string
                yield json.dumps(result, ensure_ascii=False).encode('utf-8') + b"\n"

        # Stream the response
        return StreamingResponse(result_generator(), media_type="application/json")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
