"""
Standalone Test Script untuk Pengecekan Koneksi Supabase.
Jalankan script ini di terminal:
    python test_db_connection.py
"""
import sys
import os

# Menambahkan path backend agar modul app bisa di-import
sys.path.append(os.getcwd())

try:
    from app.db.supabase import supabase_client, get_supabase_client
    from app.core.config import settings
except ImportError as e:
    print(f"❌ Error Import: {e}")
    print("Pastikan Anda menjalankan script ini dari folder 'backend' dan venv aktif.")
    sys.exit(1)

def test_connection():
    print("=" * 50)
    print("🚀 EDU-SOLVE AI: Database Connection Test")
    print("=" * 50)
    print(f"🔗 URL: {settings.SUPABASE_URL}")
    print("-" * 50)

    if supabase_client is None:
        print("❌ SKIPPED: Client tidak terinisialisasi.")
        print("💡 Cek file .env anda. Pastikan URL dan KEY sudah benar.")
        return

    try:
        # 1. Test query sederhana ke tabel 'documents'
        # Kita mencoba menghitung jumlah baris (count)
        print("📡 Mencoba query ke tabel 'documents'...")
        # Note: Menggunakan execute() untuk mendapatkan response dari supabase-py
        response = supabase_client.table("documents").select("*", count="exact").limit(1).execute()
        
        row_count = response.count if hasattr(response, 'count') and response.count is not None else "Unknown"
        print(f"✅ KONEKSI BERHASIL!")
        print(f"📊 Jumlah baris di tabel 'documents': {row_count}")

    except Exception as e:
        print("❌ KONEKSI GAGAL / ERROR!")
        # Menangani error dari postgrest atau network
        if hasattr(e, 'message'):
            print(f"Pesan: {e.message}")
        else:
            print(f"Detail: {type(e).__name__} - {str(e)}")
    
    print("-" * 50)

if __name__ == "__main__":
    test_connection()
