from pydantic import BaseModel
from typing import Dict, Any

class OCRUploadResponse(BaseModel):
    success: bool
    message: str
    filename: str
    stats: Dict[str, Any]
