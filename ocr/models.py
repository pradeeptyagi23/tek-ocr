from pydantic import BaseModel
from typing import List


class OCRPage(BaseModel):
    """
    Model representing a single page of an OCR document.

    Attributes:
        page_number (int): The number of the page within the document.
        text (str): The extracted text from the page.
    """

    page_number: int
    text: str


class OCRDocument(BaseModel):
    """
    Model representing an entire OCR document.

    Attributes:
        document_id (str): A unique identifier for the document.
        pages (List[OCRPage]): A list of pages in the document.
    """

    document_id: str
    pages: List[OCRPage]
