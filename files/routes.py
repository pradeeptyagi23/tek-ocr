from fastapi import APIRouter, Depends
from files.utils import upload_file_async
from files.models import FileLocations
from auth.utils import get_current_user
import os
import asyncio,aioboto3
file_router = APIRouter()


@file_router.post('/upload-files/')
async def upload_files(file_locations: FileLocations, current_user: str = Depends(get_current_user)):
    signed_urls = []

    session = aioboto3.Session(region_name=os.getenv("AWS_REGION"))
    async with session.client('s3') as s3_client:
        upload_tasks = [upload_file_async(file_path.path,s3_client) for file_path in file_locations.files]

        signed_urls = await asyncio.gather(*upload_tasks)

    return {"signed_urls":signed_urls}
