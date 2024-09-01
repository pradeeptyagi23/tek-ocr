from pydantic import BaseModel
from typing import List

class FileLocation(BaseModel):
    path: str
    description: str = None

class FileLocations(BaseModel):
    files: List[FileLocation]
