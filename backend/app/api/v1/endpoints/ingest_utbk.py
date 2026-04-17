"""
Admin Endpoint untuk UTBK PDF Ingestion dengan Gemini Vision.

Endpoints:
- POST /api/v1/admin/ingest-utbk
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

from app.services.ingest_utbk import ingest_pdf_utbk_pipeline

router = APIRouter(prefix="/admin", tags=["admin"])


class IngestUTBKRequest(BaseModel):
    """Request body untuk UTBK ingest endpoint."""
    pdf_dir: Optional[str] = "/app/data"


class IngestUTBKResponse(BaseModel):
    """Response dari UTBK ingest endpoint."""
    success: bool
    message: str
    stats: dict


@router.post("/ingest-utbk", response_model=IngestUTBKResponse)
async def ingest_utbk_pdfs(request: IngestUTBKRequest) -> IngestUTBKResponse:
    """
    Trigger UTBK PDF ingestion pipeline dengan Gemini Vision OCR.
    
    Pipeline steps:
    1. Extract images dari PDF files
    2. Send ke Gemini 1.5 Vision untuk OCR + metadata extraction
    3. Auto-detect: subject, topic, difficulty, type, correct answer
    4. Generate embeddings (Google text-embedding-004)
    5. Upload ke Supabase tabel `documents`
    
    Args:
        request: IngestUTBKRequest dengan pdf_dir path
        
    Returns:
        IngestUTBKResponse dengan success status dan statistics
        
    Raises:
        HTTPException 400: Jika ada error di pipeline
    """
    try:
        # Validasi path
        if not os.path.exists(request.pdf_dir):
            raise HTTPException(
                status_code=400,
                detail=f"PDF directory tidak ditemukan: {request.pdf_dir}"
            )
        
        # Run pipeline
        result = ingest_pdf_utbk_pipeline(pdf_dir=request.pdf_dir)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
        
        return IngestUTBKResponse(
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
