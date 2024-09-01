from pydantic import BaseModel
from typing import List

class OCRPage(BaseModel):
    page_number: int
    text: str

class OCRDocument(BaseModel):
    document_id: str
    pages: List[OCRPage]
