"""
Supabase Client Module.
Menyediakan koneksi ke Supabase menggunakan library `supabase-py`.

File ini terpisah dari `session.py` (SQLAlchemy) karena tanggung jawab berbeda:
- session.py  → ORM / migrasi Alembic (koneksi langsung ke PostgreSQL)
- supabase.py → Supabase REST API, RPC calls, vector search (via PostgREST)

Usage:
    from app.db.supabase import get_supabase_client

    # Sebagai dependency injection di endpoint FastAPI
    @router.get("/")
    async def my_endpoint(sb = Depends(get_supabase_client)):
        result = sb.table("documents").select("*").execute()

    # Atau dipanggil langsung di service layer
    from app.db.supabase import supabase_client
    result = supabase_client.table("documents").select("*").execute()
"""
from supabase import create_client, Client
from app.core.config import settings


def _init_supabase_client() -> Client:
    """
    Inisialisasi Supabase Client.

    Melakukan validasi bahwa SUPABASE_URL dan SUPABASE_KEY
    sudah diisi (bukan nilai default/placeholder dari .env.example).

    Returns:
        Supabase Client instance.

    Raises:
        ValueError: Jika kredensial Supabase belum dikonfigurasi.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY

    # Validasi: cegah koneksi dengan kredensial placeholder
    placeholder_values = [
        "https://your-project.supabase.co",
        "your-anon-key",
        "",
    ]

    if url in placeholder_values or key in placeholder_values:
        raise ValueError(
            "Kredensial Supabase belum dikonfigurasi. "
            "Isi SUPABASE_URL dan SUPABASE_KEY di file .env "
            "dengan nilai asli dari dashboard Supabase."
        )

    # Buat client — supabase-py menangani autentikasi otomatis
    client = create_client(url, key)
    return client


# === Singleton Instance ===
# Client di-inisialisasi saat modul di-import.
# Jika .env belum diisi, akan raise ValueError yang jelas di console.
try:
    supabase_client: Client = _init_supabase_client()
except ValueError as e:
    # Jangan crash seluruh app — biarkan modul lain tetap jalan.
    # Service yang butuh Supabase akan mendapat error saat dipanggil.
    print(f"[Supabase] ⚠️  {str(e)}")
    supabase_client = None  # type: ignore


def get_supabase_client() -> Client:
    """
    Dependency injection untuk FastAPI endpoint.
    Mengembalikan Supabase client instance.

    Contoh penggunaan di endpoint:
        @router.get("/data")
        async def get_data(sb: Client = Depends(get_supabase_client)):
            ...

    Raises:
        RuntimeError: Jika client belum terinisialisasi (kredensial salah/kosong).
    """
    if supabase_client is None:
        raise RuntimeError(
            "Supabase client belum terinisialisasi. "
            "Pastikan SUPABASE_URL dan SUPABASE_KEY di .env sudah benar."
        )
    return supabase_client
