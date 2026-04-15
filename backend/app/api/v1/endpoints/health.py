from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.supabase import get_supabase_client
import time

router = APIRouter()

@router.get("/db")
async def check_db_health(
    sb: Client = Depends(get_supabase_client)
):
    """
    Endpoint untuk mengecek status koneksi ke Supabase.
    Melakukan query ringan ke tabel 'documents'.
    """
    start_time = time.time()
    try:
        # Melakukan query minimal untuk memastikan koneksi aktif
        # Kita hanya mengambil 1 baris (atau 0 baris dengan limit 0)
        response = sb.table("documents").select("id").limit(1).execute()
        
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        return {
            "status": "ok",
            "database": "connected",
            "latency_ms": latency_ms,
            "message": "Koneksi ke Supabase berhasil."
        }
    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        # Jika gagal, kita return status error tapi tetap 200 OK di level HTTP
        # agar monitoring system bisa membedakan app alive vs db down.
        # Atau bisa menggunakan 503 Service Unavailable jika ingin memicu alert.
        return {
            "status": "error",
            "database": "disconnected",
            "latency_ms": latency_ms,
            "error": str(e),
            "message": "Gagal terhubung ke Supabase."
        }
