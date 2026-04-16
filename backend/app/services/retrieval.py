"""
Service untuk Retrieval Vektor dari Supabase.
Mengambil dokumen paling relevan berdasarkan kesamaan vektor (vector similarity).

Asumsi:
- Tabel `documents` sudah ada di Supabase dengan kolom:
    id (uuid), content (text), embedding (vector(768)), metadata (jsonb)
- RPC function `match_documents` sudah dibuat di Supabase (SQL di bawah).
"""
from app.db.supabase import supabase_client


# ============================================================
# STUB: Fungsi placeholder untuk generate embedding dari teks.
# Akan diganti dengan model embedding nyata (misal Gemini Embedding)
# di iterasi berikutnya oleh tim Data Ingestion.
# Saat ini mengembalikan vektor nol berdimensi 768 (sesuai schema).
# ============================================================
async def get_embedding(text: str) -> list[float]:
    """
    Placeholder — menghasilkan vektor dummy 768 dimensi.

    TODO: Ganti dengan pemanggilan nyata ke embedding model, contoh:
      - Google Gemini Embedding API (text-embedding-004)
      - Atau model embedding lain yang menghasilkan vektor 768 dimensi
    """
    return [0.0] * 768


async def retrieve_context(query_text: str, top_k: int = 3) -> list[str]:
    """
    Mengambil dokumen paling relevan dari Supabase menggunakan vector similarity search.
    Memanggil RPC function 'match_documents' yang ada di database.

    Args:
        query_text: Pertanyaan atau teks dari user.
        top_k: Jumlah dokumen teratas yang diambil (default: 3).

    Returns:
        list berisi isi teks (content) dari dokumen paling relevan.
    """

    if supabase_client is None:
        print("[Retrieval] Warning: Supabase client tidak aktif. Melewati tahap retrieval.")
        return []

    try:
        # 1. Dapatkan embedding vektor dari teks query
        query_embedding = await get_embedding(query_text)

        # 2. Panggil RPC `match_documents` di Supabase
        # RPC ini diasumsikan menerima argumen: query_embedding (vector) dan match_count (int)
        response = supabase_client.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_count": top_k,
            }
        ).execute()

        # 3. Parse hasil
        # response.data berisi list of documents yang cocok
        results = response.data

        if not results:
            return []

        # Ambil teks konten dari setiap dokumen yang cocok
        context_docs = [
            doc.get("content", "")
            for doc in results
            if doc.get("content")
        ]

        return context_docs

    except Exception as e:
        # Error handling agar pipeline utama tidak crash jika retrieval gagal
        print(f"[Retrieval] Error saat melakukan retrieval: {str(e)}")
        return []

