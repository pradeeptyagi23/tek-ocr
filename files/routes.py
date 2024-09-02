from fastapi import APIRouter, Depends
from files.utils import upload_file_async
from files.models import FileLocations
from auth.utils import get_current_user
import os
import asyncio
import aioboto3
from typing import Dict, List

file_router = APIRouter()


@file_router.post("/upload-files/")
async def upload_files(
    file_locations: FileLocations, current_user: str = Depends(get_current_user)
) -> Dict[str, List[str]]:
    """
    Endpoint to upload multiple files and get signed URLs.

    Args:
        file_locations (FileLocations): A list of file locations
        with paths and optional descriptions.
        current_user (str): The username of the currently authenticated user.

    Returns:
        dict: A dictionary containing the signed URLs of the uploaded files.
    """
    signed_urls = []

    session = aioboto3.Session(region_name=os.getenv("AWS_REGION"))
    async with session.client("s3") as s3_client:
        # Create a list of upload tasks
        upload_tasks = [
            upload_file_async(file_path.path, s3_client)
            for file_path in file_locations.files
        ]

        # Await and gather all upload tasks
        signed_urls = await asyncio.gather(*upload_tasks)

    return {"signed_urls": signed_urls}
