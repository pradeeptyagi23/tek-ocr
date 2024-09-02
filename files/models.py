from pydantic import BaseModel
from typing import List, Optional


class FileLocation(BaseModel):
    """
    Model for representing a single file location.

    Attributes:
        path (str): The file path.
        description (Optional[str]): An optional description of the file.
    """

    path: str
    description: Optional[str] = None


class FileLocations(BaseModel):
    """
    Model for representing a list of file locations.

    Attributes:
        files (List[FileLocation]): A list of file locations.
    """

    files: List[FileLocation]
