import hashlib
import os
from fastapi import HTTPException

# AWS S3 Configuration
bucket_name = "tek-file-bucket"


async def file_exists(s3_client, file_key: str) -> bool:
    """
    Check if a file exists in the S3 bucket.

    Args:
        s3_client: The S3 client instance.
        file_key (str): The key of the file to check.

    Returns:
        bool: True if the file exists, False otherwise.

    Raises:
        HTTPException: If an error occurs while checking file existence.
    """
    try:
        await s3_client.head_object(Bucket=bucket_name, Key=file_key)
        return True
    except s3_client.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            print(f"Got error {e.response}")
            raise HTTPException(status_code=500, detail="Error checking file existence")


async def upload_file_async(file_path: str, s3_client) -> str:
    """
    Upload a file to S3 asynchronously and return a signed URL.

    Args:
        file_path (str): The path of the file to upload.
        s3_client: The S3 client instance.

    Returns:
        str: The signed URL for the uploaded file.

    Raises:
        HTTPException: If the file does not exist or if the upload fails.
    """
    try:
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=400, detail=f"File not found: {file_path}")

        print(f"Got file path {file_path}")

        # Compute file hash
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()

        file_key = f"{file_hash}/{os.path.basename(file_path)}"

        if await file_exists(s3_client, file_key):
            return f"File already exists: {file_key}"

        await s3_client.upload_file(file_path, bucket_name, file_key)

        signed_url = await s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": file_key},
            ExpiresIn=3600,
        )
        return signed_url

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload {file_path}: {str(e)}"
        )
