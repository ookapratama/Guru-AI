"""
Endpoint utama POST /solve.
Merangkai seluruh pipeline: Schema → Retrieval → Prompt → Gemini → Save → Response.

Alur:
1. Terima SolveRequest dari Frontend
2. Jalankan retrieve_context() → dapat context docs (RAG)
3. Jalankan build_prompt() → dapat super prompt
4. Jalankan call_gemini() → dapat structured answer dari AI
5. Simpan record ke tabel `questions` di Supabase
6. Return SolveResponse ke Frontend
"""
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.solve import SolveRequest, SolveResponse
from app.services.retrieval import retrieve_context
from app.services.gemini import build_prompt, call_gemini

router = APIRouter()


@router.post("/", response_model=SolveResponse)
async def solve_problem(request: SolveRequest):
    """
    Endpoint utama untuk menyelesaikan soal.
    Menerima foto soal (base64) + pertanyaan teks, mengembalikan solusi terstruktur.
    """

    # Generate ID unik untuk sesi pertanyaan ini
    question_id = uuid.uuid4()

    # --- STEP 1: Retrieval — Ambil dokumen relevan dari Supabase (RAG) ---
    try:
        context_docs = await retrieve_context(request.query_text)
    except Exception as e:
        # Retrieval gagal bukan alasan untuk menghentikan proses.
        # Gemini tetap bisa menjawab tanpa konteks RAG.
        print(f"[Solve] Warning: Retrieval gagal, lanjut tanpa konteks. Detail: {str(e)}")
        context_docs = []

    # --- STEP 2: Prompt Engineering — Rakit super prompt ---
    prompt = build_prompt(
        query_text=request.query_text,
        context_docs=context_docs,
        subject=request.subject,
    )

    # --- STEP 3: Gemini — Panggil AI untuk menyelesaikan soal ---
    try:
        ai_result = await call_gemini(
            prompt=prompt,
            image_base64=request.image_base64,
        )
    except ValueError as e:
        # Error parsing (gambar invalid, JSON response rusak, dll)
        raise HTTPException(
            status_code=422,
            detail=f"Gagal memproses soal. {str(e)}"
        )
    except Exception as e:
        # Error koneksi ke Gemini API
        raise HTTPException(
            status_code=502,
            detail=f"Gagal menghubungi AI service. {str(e)}"
        )

    # --- STEP 4: Simpan ke Supabase tabel `questions` ---
    await _save_question_record(
        question_id=question_id,
        request=request,
        ai_result=ai_result,
        references_used=context_docs,
    )

    # --- STEP 5: Return response ke Frontend ---
    return SolveResponse(
        status="success",
        question_id=question_id,
        concept=ai_result["concept"],
        steps=ai_result["steps"],
        final_answer=ai_result["final_answer"],
        references_used=context_docs if context_docs else [],
    )


async def _save_question_record(
    question_id: uuid.UUID,
    request: SolveRequest,
    ai_result: dict,
    references_used: list,
) -> None:
    """
    Simpan seluruh record pertanyaan + jawaban ke tabel `questions` di Supabase.
    Proses ini bersifat fire-and-forget: jika gagal simpan, endpoint tetap
    mengembalikan response ke user (tidak blocking).

    Schema tabel `questions`:
        id (uuid), query_text (text), image_base64 (text), subject (text),
        concept (text), steps (text), final_answer (text),
        references_used (jsonb), created_at (timestamptz)
    """

    record = {
        "id": str(question_id),
        "query_text": request.query_text,
        "image_base64": request.image_base64,
        "subject": request.subject,
        "concept": ai_result.get("concept", ""),
        "steps": ai_result.get("steps", ""),
        "final_answer": ai_result.get("final_answer", ""),
        "references_used": references_used,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Simpan via Supabase REST API
    url = f"{settings.SUPABASE_URL}/rest/v1/questions"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",  # Tidak perlu return data, hemat bandwidth
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=record, headers=headers)
            response.raise_for_status()

    except Exception as e:
        # Gagal simpan TIDAK menghentikan response ke user
        # Log error untuk monitoring, tapi proses tetap lanjut
        print(
            f"[Solve] Warning: Gagal simpan ke Supabase. "
            f"question_id={question_id}. Detail: {str(e)}"
        )
