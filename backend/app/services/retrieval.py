"""
Service untuk Retrieval Vektor dari Supabase.
Mengambil dokumen paling relevan berdasarkan kesamaan vektor (vector similarity).

Asumsi:
- Tabel `documents` sudah ada di Supabase dengan kolom:
    id (uuid), content (text), embedding (vector(768)), metadata (jsonb)
- RPC function `match_documents` sudah dibuat di Supabase (SQL di bawah).
"""
import httpx
from typing import List
from app.core.config import settings


# ============================================================
# STUB: Fungsi placeholder untuk generate embedding dari teks.
# Akan diganti dengan model embedding nyata (misal Gemini Embedding)
# di iterasi berikutnya oleh tim Data Ingestion.
# Saat ini mengembalikan vektor nol berdimensi 768 (sesuai schema).
# ============================================================
async def get_embedding(text: str) -> List[float]:
    """
    Placeholder — menghasilkan vektor dummy 768 dimensi.

    TODO: Ganti dengan pemanggilan nyata ke embedding model, contoh:
      - Google Gemini Embedding API (text-embedding-004)
      - Atau model embedding lain yang menghasilkan vektor 768 dimensi
    """
    return [0.0] * 768


async def retrieve_context(query_text: str, top_k: int = 3) -> List[str]:
    """
    Mengambil dokumen paling relevan dari Supabase berdasarkan
    kesamaan vektor (cosine similarity) terhadap query user.

    Args:
        query_text: Pertanyaan atau teks dari user.
        top_k: Jumlah dokumen teratas yang diambil (default: 3).

    Returns:
        List berisi isi teks (content) dari dokumen paling relevan.
        Mengembalikan list kosong jika gagal atau tidak ada dokumen.

    Flow:
        1. Konversi query_text -> embedding vektor via get_embedding()
        2. Panggil RPC `match_documents` di Supabase via REST API
        3. Ambil field `content` dari hasil pencarian
    """

    # 1. Dapatkan embedding vektor dari teks query
    query_embedding = await get_embedding(query_text)

    # 2. Panggil Supabase RPC endpoint via httpx (async)
    # RPC `match_documents` menerima: query_embedding, match_count
    rpc_url = f"{settings.SUPABASE_URL}/rest/v1/rpc/match_documents"

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "query_embedding": query_embedding,
        "match_count": top_k,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                rpc_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        # 3. Parse hasil — ambil field `content` dari setiap dokumen
        results = response.json()

        if not results:
            return []

        # Ambil teks konten dari setiap dokumen yang cocok
        context_docs = [
            doc.get("content", "")
            for doc in results
            if doc.get("content")  # skip dokumen tanpa konten
        ]

        return context_docs

    except httpx.HTTPStatusError as e:
        # Error dari Supabase (4xx/5xx) — log dan return kosong
        print(f"[Retrieval] Supabase HTTP error: {e.response.status_code} - {e.response.text}")
        return []

    except httpx.RequestError as e:
        # Error koneksi (timeout, DNS, dll) — log dan return kosong
        print(f"[Retrieval] Koneksi error ke Supabase: {str(e)}")
        return []

    except Exception as e:
        # Error tidak terduga — log dan return kosong
        print(f"[Retrieval] Error tidak terduga: {str(e)}")
        return []
