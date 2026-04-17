# UTBK PDF Ingestion dengan Gemini Vision API

Panduan lengkap untuk setup dan menjalankan UTBK PDF ingestion menggunakan Google Gemini 1.5 Vision API.

## Overview

Pipeline ini dirancang khusus untuk soal-soal UTBK (image-based PDF):

```
PDF (Soal UTBK Scan)
    ↓
Extract Images (per halaman) - Pillow
    ↓
Send to Gemini 1.5 Vision (OCR + metadata extraction)
    ↓
Auto-detect: Subject, Topic, Difficulty, Type, Answer
    ↓
Generate Embeddings (Google text-embedding-004)
    ↓
Upload ke Supabase → Vector Search Ready
```

## Key Features

✅ **No Heavy Libraries** - Gunakan Pillow (sudah ada) + Gemini API
✅ **High Accuracy** - Gemini Vision lebih akurat dari local OCR
✅ **Auto-Metadata** - Gemini auto-detect subject, topic, difficulty, type
✅ **Free Tier** - 15,000 requests/month dari Google
✅ **Simple Setup** - Hanya butuh PDF files + Docker

---

## Prerequisites

### 1. Check Requirements

Library yang dibutuhkan sudah ada di `backend/requirements.txt`:

```bash
cat backend/requirements.txt | grep -E "Pillow|google|langchain"
```

Should show:
- ✓ Pillow>=10.0.0
- ✓ google-generativeai>=0.4.1
- ✓ google-genai>=0.3.0
- ✓ langchain (dan dependencies)

**No need untuk pdf2image atau easyocr** - Gemini API handle-nya!

### 2. Environment Setup

Verify `.env` memiliki:

```env
GOOGLE_API_KEY=your_api_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
```

### 3. Docker Running

```bash
docker-compose up -d
```

---

## Usage

### Option 1: CLI via docker-compose exec (RECOMMENDED)

```bash
# 1. Add PDF files ke backend/data/
cp utbk_math_2024.pdf backend/data/
cp utbk_english_2024.pdf backend/data/

# 2. Run ingest script
docker-compose exec api python ingest_utbk.py

# Dengan custom PDF directory:
docker-compose exec api python ingest_utbk.py --pdf-dir /app/data
```

**Expected Output:**

```
======================================================================
EduSolve AI — UTBK PDF Ingestion (Gemini Vision)
======================================================================

[STEP 1] Find PDF files...
[INFO] Found 2 PDF file(s)

[STEP 2] Extract images and process via Gemini Vision...

[PROCESSING] utbk_math_2024.pdf...
[INFO] Extract images dari utbk_math_2024.pdf...
  ✓ 8 images extracted
  [Vision] Page 0...✓ Math - Trigonometry
  [Vision] Page 1...✓ Math - Algebra
  [Vision] Page 2...✓ Math - Geometry
  ...

[PROCESSING] utbk_english_2024.pdf...
[INFO] Extract images dari utbk_english_2024.pdf...
  ✓ 12 images extracted
  [Vision] Page 0...✓ English - Reading Comprehension
  ...

[STEP 3] Generate embeddings dan upload ke Supabase...
[INFO] Inisialisasi embeddings (models/text-embedding-004)...
[INFO] Uploading 20 soal ke Supabase...
[SUCCESS] Berhasil upload 20 soal

======================================================================
✓ SUCCESS: Berhasil ingest 20 soal UTBK via Gemini Vision

Statistics:
  • PDF Files: 2
  • Soal Extracted: 20
  • Soal Uploaded: 20
======================================================================
```

### Option 2: Via API Endpoint

Jika server running, trigger via FastAPI Swagger:

```
POST /api/v1/admin/ingest-utbk
```

Access: http://localhost:8000/docs

**Request Body:**
```json
{
  "pdf_dir": "/app/data"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Berhasil ingest 20 soal UTBK via Gemini Vision",
  "stats": {
    "pdf_files": 2,
    "soal_count": 20,
    "uploaded": 20
  }
}
```

### Option 3: Local CLI (Development)

```bash
cd backend
python ingest_utbk.py --pdf-dir ./data
```

---

## File Structure

```
backend/
├── ingest_utbk.py                         ← CLI entry point
├── data/
│   ├── utbk_math_2024.pdf                 ← Your PDF files
│   └── utbk_english_2024.pdf
├── app/
│   ├── services/
│   │   └── ingest_utbk.py                 ← Core service (Gemini Vision OCR)
│   └── api/v1/endpoints/
│       └── ingest_utbk.py                 ← API endpoint
├── INGEST_UTBK.md                         ← This file
└── requirements.txt                       ← Already has all dependencies!
```

---

## How It Works

### Step 1: Extract Images

- Read PDF file
- Extract each page as PIL Image
- Use Pillow (lightweight, already in requirements)

### Step 2: Gemini Vision OCR + Metadata

For each image:
- Convert to base64
- Send to Gemini 1.5 Flash dengan prompt
- Gemini extracts:
  - **soal_text**: Complete problem text
  - **subject**: Math or English
  - **topic**: Specific area (e.g., Trigonometry, Grammar)
  - **difficulty**: Easy / Medium / Hard
  - **type**: multiple_choice / essay
  - **correct_answer**: Jawaban benar (jika terlihat)

### Step 3: Create LangChain Documents

Combine OCR text + metadata:
- **Content**: Combined text + metadata fields
- **Metadata**: subject, topic, difficulty, type, soal_id, source_file, etc.

### Step 4: Generate Embeddings

- Use Google Embedding API (text-embedding-004)
- Generate 768-dimensional vectors
- Ready untuk vector similarity search

### Step 5: Upload to Supabase

- Store di tabel `documents`
- Columns: id, content, embedding, metadata
- Metadata stored as JSONB untuk filtering

---

## Cost Analysis

### Gemini 1.5 Flash (Free Tier)

| Item | Quota |
|------|-------|
| Requests/month | 15,000 |
| Per request cost | $0 (free tier) |
| Per problem (1 image) | 1 request |
| **Capacity** | **~15,000 problems/month** |

Example:
- 100 soal = ~100 requests = FREE ✓
- 1000 soal = ~1000 requests = FREE ✓
- 15000 soal = 15000 requests = At limit

**Estimate for typical UTBK set (200 soal):** Completely FREE

---

## API Limits & Quotas

**Google Gemini API Free Tier:**
- 15,000 RPM (requests per minute) - effectively unlimited
- 15,000 requests/month total for free tier
- After free tier: $0.075 per 1M input tokens

**Recommendation for UTBK:**
- One-time ingest: 100-500 soal = fully free
- If need more: Upgrade to paid tier (~$0.001 per soal)

---

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'google.genai'`

**Solution:** Already in requirements, rebuild Docker:
```bash
docker-compose down
docker-compose up -d --build
```

### Error: `PDF directory tidak ditemukan`

**Solution:** Check PDF location:
```bash
docker-compose exec api ls -la /app/data/
# Harusnya ada file *.pdf
```

### Error: `GOOGLE_API_KEY belum dikonfigurasi`

**Solution:** Verify .env:
```bash
docker-compose exec api cat .env | grep GOOGLE_API_KEY
# Should show your API key
```

### Warning: `No soal text extracted`

Possible causes:
- Image kualitas terlalu rendah
- Soal dengan banyak formula/diagram (Gemini limited)
- PDF corrupted

**Solution:**
- Verify PDF readable dengan human eye
- Try dengan sample PDF dulu
- Check Gemini response di logs

### Gemini API Rate Limited

If too many requests:

**Solution:** 
- Upgrade Google API tier
- Or spread ingestion over multiple days
- Or batch process with delays

---

## Performance Notes

- **Per Image Processing:** ~1-2 seconds (Gemini API latency)
- **Batch Example:** 20 pages = ~30-40 seconds total
- **First Run:** Might be slower (model initialization)

**Tips untuk optimization:**
- Batch multiple ingestions
- Use batch API jika available (upcoming)
- Handle connection timeouts gracefully

---

## Next Steps

1. ✓ Verify Docker running
2. ✓ Add PDF files ke `backend/data/`
3. ✓ Run: `docker-compose exec api python ingest_utbk.py`
4. ✓ Wait for completion
5. ✓ Verify in Supabase → table `documents` punya soal baru dengan embeddings
6. ✓ Test `/solve` endpoint dengan screenshot soal

---

## API Reference

### Endpoint: POST /api/v1/admin/ingest-utbk

**Request:**
```json
{
  "pdf_dir": "/app/data"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Berhasil ingest 20 soal UTBK via Gemini Vision",
  "stats": {
    "pdf_files": 2,
    "soal_count": 20,
    "uploaded": 20
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "message": "PDF directory tidak ditemukan: /app/data",
  "stats": {
    "pdf_files": 0,
    "soal_count": 0,
    "uploaded": 0
  }
}
```

---

## Questions?

Refer to:
- Service logic: `backend/app/services/ingest_utbk.py`
- CLI script: `backend/ingest_utbk.py`
- API endpoint: `backend/app/api/v1/endpoints/ingest_utbk.py`
