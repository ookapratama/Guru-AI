# 📘 Panduan Testing & Integrasi Database (Untuk Dayat)

Halo Dayat! Bagian Core Backend sudah siap untuk diintegrasikan dengan data dokumen yang sedang kamu siapkan. Berikut adalah langkah-langkah untuk memastikan segalanya berjalan lancar.

---

## 1. Persiapan Database (Supabase)

Pastikan tabel `documents` sudah memiliki skema berikut di editor SQL Supabase:

```sql
create table documents (
  id uuid primary key default uuid_generate_v4(),
  content text not null,
  embedding vector(768), -- Sesuaikan dengan dimensi model (768 untuk Gemini)
  metadata jsonb,
  created_at timestamptz default now()
);
```

### 2. Buat RPC Function (WAJIB)
Fungsi retrieval di backend menggunakan RPC `match_documents`. Harap jalankan SQL ini di dashboard Supabase kamu:

```sql
create or replace function match_documents (
  query_embedding vector(768),
  match_count int
)
returns table (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  order by documents.embedding <=> query_embedding
  limit match_count;
end;
$$;
```

---

## 2. Cara Testing Diagnostik

Setelah kamu mengisi data dokumen ke database, gunakan dua alat ini untuk memastikan koneksi:

### A. Skrip Terminal (Cepat)
Gunakan skrip ini untuk cek jumlah data tanpa harus buka browser.
1. Masuk ke folder `backend`.
2. Jalankan: `python test_db_connection.py`
   - **Sukses:** Akan muncul jumlah baris data di tabel `documents`.
   - **Gagal:** Muncul pesan error kredensial.

### B. Health Check API (Monitoring)
Sambil menjalankan server (`uvicorn app.main:app`), buka browser atau Postman:
- `GET http://localhost:8000/api/v1/health/db`
- Respons yang diharapkan:
  ```json
  {
    "status": "ok",
    "database": "connected",
    "latency_ms": 120.5
  }
  ```

---

## 3. Flow Pengujian RAG

Untuk menguji apakah data yang kamu input berhasil ditarik oleh AI:
1. Hit endpoint `POST http://localhost:8000/api/v1/solve/`.
2. Kirim JSON bodi (minimal):
   ```json
   {
     "image_base64": "...",
     "query_text": "Apa isi dokumen tentang materi turunan?"
   }
   ```
3. Cek respons di field `references_used`. Jika datamu berhasil ditarik, teks dokumennya akan muncul di sana.

---

## 📝 Catatan Penting
- Pastikan file `.env` di lokal kamu sudah berisi `SUPABASE_URL` dan `SUPABASE_KEY` yang benar.
- Jika dimensi vektor model berubah, sesuaikan parameter `vector(768)` di SQL dan script retrieval.

Semangat integrasinya, Dayat! 🚀
