"""
Endpoint untuk PDF Ingestion.
Admin-only endpoint untuk trigger PDF ingestion pipeline via FastAPI.

Endpoints:
- POST /api/v1/admin/ingest
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import asyncio
import os

from app.services.ingest import ingest_pdf_pipeline, process_uploaded_file_ocr
from app.schemas.ingest import OCRUploadResponse

router = APIRouter(prefix="/admin", tags=["admin"])


class IngestRequest(BaseModel):
    """Request body untuk ingest endpoint."""
    data_dir: Optional[str] = "./data"


class IngestResponse(BaseModel):
    """Response dari ingest endpoint."""
    success: bool
    message: str
    stats: dict


@router.post("/ingest", response_model=IngestResponse)
async def ingest_pdfs(request: IngestRequest) -> IngestResponse:
    """
    Trigger PDF ingestion pipeline.
    
    Pipeline steps:
    1. Load all PDFs dari data_dir
    2. Split documents into chunks
    3. Generate embeddings (Google text-embedding-004)
    4. Upload ke Supabase tabel `documents`
    
    Args:
        request: IngestRequest dengan optional data_dir
        
    Returns:
        IngestResponse dengan success status dan statistics
        
    Raises:
        HTTPException 400: Jika ada error di pipeline
    """
    try:
        # Validasi path
        if not os.path.exists(request.data_dir):
            raise HTTPException(
                status_code=400,
                detail=f"Direktori tidak ditemukan: {request.data_dir}"
            )
        
        # Run pipeline
        result = await ingest_pdf_pipeline(request.data_dir)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
        
        return IngestResponse(
            success=result["success"],
            message=result["message"],
            stats=result["stats"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/upload-ocr", response_model=OCRUploadResponse)
async def upload_pdf_ocr(file: UploadFile = File(...)) -> OCRUploadResponse:
    """
    Ekstrak teks PDF/Image menggunakan Gemini 1.5 Flash (OCR) dan save vector embeddings.
    Endpoint ini menerima 1 file upload dan mengembalikan stats penyimpanan vector di tabel \`documents\`.
    """
    try:
        # Validasi ekstensi
        valid_extensions = [".pdf", ".jpg", ".jpeg", ".png"]
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in valid_extensions:
            raise HTTPException(
                status_code=400, 
                detail="Format file tidak didukung. Gunakan PDF atau Image (jpg/png)."
            )
            
        file_bytes = await file.read()
        mime_type = file.content_type
        
        # Eksekusi pipeline di service layer
        result = await process_uploaded_file_ocr(
            file_bytes=file_bytes,
            filename=file.filename,
            mime_type=mime_type
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400, 
                detail=result["message"]
            )
            
        return OCRUploadResponse(
            success=result["success"],
            message=result["message"],
            filename=result["filename"],
            stats=result["stats"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

