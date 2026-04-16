# Backend Ingestion Setup

Panduan untuk menjalankan PDF ingestion pipeline menggunakan Docker.

## Quick Start

### Option 1: Via Docker Exec (Recommended)

```bash
# 1. Letakkan PDF files ke folder data/
cp your_file.pdf ./data/

# 2. Run ingest script di dalam container
docker-compose exec api python ingest_pdf.py
```

**Output:**
```
======================================================================
EduSolve AI — PDF Ingestion Pipeline (CLI)
======================================================================

[STEP 1] Load PDFs dari ./data...
[INFO] Ditemukan 2 file PDF
[PROCESSING] chapter1.pdf...
  ✓ 15 pages
[INFO] Total 27 pages

[STEP 2] Split documents...
[INFO] Total 45 chunks

[STEP 3] Ingest to Supabase...
[SUCCESS] Berhasil upload 45 chunks ke Supabase

======================================================================
✓ SUCCESS: Berhasil upload 45 chunks ke Supabase

Statistics:
  • PDF Documents: 27
  • Chunks Created: 45
  • Chunks Uploaded: 45
======================================================================
```

### Option 2: Via API Endpoint

Jika server sudah running, bisa trigger via FastAPI Swagger:

1. Open: http://localhost:8000/docs
2. Find: `POST /api/v1/admin/ingest`
3. Click "Try it out"
4. (Optional) Modify `data_dir` if PDF in different folder
5. Click "Execute"

**Response:**
```json
{
  "success": true,
  "message": "Berhasil upload 45 chunks ke Supabase",
  "stats": {
    "documents": 27,
    "chunks": 45,
    "uploaded": 45
  }
}
```

### Option 3: Via Local CLI (Development)

Jika di local environment dengan .env setup:

```bash
# From backend/ directory
cd backend
python ingest_pdf.py --data-dir ./data
```

## File Structure

```
backend/
├── app/
│   ├── services/
│   │   ├── ingest.py          ← Core ingestion logic (reusable service)
│   │   ├── ai_service.py
│   │   ├── gemini.py
│   │   └── retrieval.py
│   └── api/v1/endpoints/
│       ├── ingest.py          ← FastAPI endpoint (POST /admin/ingest)
│       ├── solve.py
│       ├── history.py
│       └── health.py
├── ingest_pdf.py              ← CLI entry point (docker exec)
└── requirements.txt

data/
├── chapter1.pdf               ← Place your PDFs here
├── chapter2.pdf
└── .gitkeep
```

## How It Works

### Pipeline Steps

1. **Load PDFs**
   - PyPDFLoader membaca semua .pdf dari `data/` directory
   - Setiap halaman menjadi Document object
   - Metadata `source_file` ditambahkan ke setiap document

2. **Split Chunks**
   - RecursiveCharacterTextSplitter split documents
   - Config: `chunk_size=1000 chars`, `chunk_overlap=100 chars`
   - Separator hierarchy: `\n\n` → `\n` → ` ` → ``

3. **Generate Embeddings**
   - Google Embedding API (`text-embedding-004`)
   - Menggunakan `GOOGLE_API_KEY` dari `.env`
   - Setiap chunk → 768-dimensional vector

4. **Upload to Supabase**
   - SupabaseVectorStore upload ke tabel `documents`
   - Columns: `id`, `content`, `embedding`, `metadata`
   - Metadata includes: `source_file`, `page_number`, dll

### Architecture

```
ingest_pdf.py (CLI)
    ↓
app/services/ingest.py (Core Logic)
    ├─ load_pdfs_from_directory()
    ├─ split_documents()
    ├─ ingest_chunks_to_supabase()
    └─ ingest_pdf_pipeline() [async]
    ↓
app/api/v1/endpoints/ingest.py (FastAPI)
    └─ POST /api/v1/admin/ingest
```

## Configuration

Semua konfigurasi di `app/services/ingest.py`:

```python
CHUNK_SIZE = 1000              # Characters per chunk
CHUNK_OVERLAP = 100            # Overlap between chunks
EMBEDDING_MODEL = "models/text-embedding-004"
VECTOR_STORE_TABLE = "documents"
```

## Environment Variables (.env)

Pastikan `.env` memiliki:

```env
# Required untuk ingest
GOOGLE_API_KEY=your_google_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key  # Alternative jika ada
```

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'langchain'`

**Solution:** Install dependencies di Docker:
```bash
docker-compose exec api pip install -r requirements.txt
```

### Error: `Missing environment variables`

**Solution:** Verify `.env` file memiliki semua required keys:
```bash
docker-compose exec api cat .env | grep GOOGLE_API_KEY
docker-compose exec api cat .env | grep SUPABASE
```

### Error: `No PDF files found`

**Solution:** Check PDF files ada di `data/` directory:
```bash
ls -la ./data/
# Harusnya ada file *.pdf
```

### Error: `Supabase connection failed`

**Solution:** Cek credentials:
1. Verify SUPABASE_URL dan SUPABASE_KEY valid
2. Check network connectivity ke Supabase
3. Ensure tabel `documents` sudah ada di Supabase dengan pgvector extension

## Docker Commands Reference

```bash
# Start containers
docker-compose up -d

# Run ingest script
docker-compose exec api python ingest_pdf.py

# View logs
docker-compose logs -f api

# Check if container running
docker-compose ps

# Stop containers
docker-compose down
```

## Next Steps

1. ✓ Setup `.env` dengan credentials
2. ✓ Start Docker: `docker-compose up -d`
3. ✓ Add sample PDFs ke `./data/`
4. ✓ Run ingestion: `docker-compose exec api python ingest_pdf.py`
5. ✓ Verify in Supabase dashboard → table `documents`
6. ✓ Test `/solve` endpoint with RAG context

## Performance Notes

- Ingestion time depends on PDF size
  - Example: 27 pages → ~2-3 seconds (with network latency)
  - Larger datasets might take longer
- Embeddings cached locally by Supabase
- Vector search uses pgvector `<=>` (cosine similarity)
