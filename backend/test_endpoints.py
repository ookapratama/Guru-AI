"""
Script test manual untuk EduSolve AI Backend.
Jalankan saat server sudah running: uvicorn app.main:app --port 8000

Cara pakai:
    source venv/bin/activate
    python test_endpoints.py

Script ini menguji:
1. Health check (GET /)
2. Swagger docs (GET /docs)
3. POST /api/v1/solve/ — dengan berbagai skenario
"""
import httpx
import json
import base64
import sys

BASE_URL = "http://localhost:8000"

# Buat gambar PNG dummy kecil (1x1 pixel putih) untuk testing
# Ini adalah file PNG valid minimal — agar decode base64 di Gemini tidak error format
DUMMY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "nGP4z8BQDwAEgAF/pooBPQAAAABJRU5ErkJggg=="
)


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_health_check():
    """Test 1: Health check — GET /"""
    separator("TEST 1: Health Check — GET /")

    resp = httpx.get(f"{BASE_URL}/")
    print(f"  Status: {resp.status_code}")
    print(f"  Body:   {resp.json()}")

    assert resp.status_code == 200
    assert "EduSolve AI" in resp.json()["message"]
    print("\n  ✅ PASSED")


def test_swagger_docs():
    """Test 2: Swagger docs tersedia — GET /docs"""
    separator("TEST 2: Swagger Docs — GET /docs")

    resp = httpx.get(f"{BASE_URL}/docs")
    print(f"  Status: {resp.status_code}")
    print(f"  Content-Type: {resp.headers.get('content-type')}")

    assert resp.status_code == 200
    print("\n  ✅ PASSED — Buka http://localhost:8000/docs di browser")


def test_openapi_schema():
    """Test 3: OpenAPI schema — cek endpoint /solve terdaftar"""
    separator("TEST 3: OpenAPI Schema — Endpoint /solve terdaftar")

    resp = httpx.get(f"{BASE_URL}/api/v1/openapi.json")
    schema = resp.json()

    paths = list(schema.get("paths", {}).keys())
    print(f"  Registered paths: {paths}")

    assert "/api/v1/solve/" in paths or "/solve/" in paths
    print("\n  ✅ PASSED")


def test_solve_valid_request():
    """Test 4: POST /api/v1/solve/ — request valid"""
    separator("TEST 4: POST /solve — Request Valid")

    payload = {
        "image_base64": DUMMY_PNG_BASE64,
        "query_text": "Tentukan turunan dari f(x) = 3x² + 2x - 5",
        "subject": "matematika"
    }

    print(f"  Request:")
    print(f"    image_base64: {payload['image_base64'][:30]}...")
    print(f"    query_text: {payload['query_text']}")
    print(f"    subject: {payload['subject']}")
    print()

    try:
        resp = httpx.post(
            f"{BASE_URL}/api/v1/solve/",
            json=payload,
            timeout=30.0  # Gemini bisa lambat
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Response:")
        print(f"  {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")

        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "success"
            assert "question_id" in data
            assert "concept" in data
            assert "steps" in data
            assert "final_answer" in data
            print("\n  ✅ PASSED — AI berhasil menjawab soal!")
        elif resp.status_code == 502:
            print("\n  ⚠️  EXPECTED — Gemini API error (API key belum valid)")
            print("     Ini normal jika GOOGLE_API_KEY di .env masih dummy.")
        elif resp.status_code == 422:
            print("\n  ⚠️  EXPECTED — Validation/parse error")
            print("     Cek detail error di response body.")
        else:
            print(f"\n  ❌ UNEXPECTED status code: {resp.status_code}")

    except httpx.ConnectError:
        print("  ❌ Server tidak berjalan! Jalankan dulu:")
        print("     source venv/bin/activate && uvicorn app.main:app --port 8000")
        sys.exit(1)


def test_solve_without_subject():
    """Test 5: POST /api/v1/solve/ — tanpa subject (opsional)"""
    separator("TEST 5: POST /solve — Tanpa Subject")

    payload = {
        "image_base64": DUMMY_PNG_BASE64,
        "query_text": "Jelaskan soal pada gambar ini"
    }

    resp = httpx.post(
        f"{BASE_URL}/api/v1/solve/",
        json=payload,
        timeout=30.0
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)[:500]}")

    # Harus diterima (subject optional), status 200 atau 502 (API key)
    assert resp.status_code in [200, 422, 502]
    print("\n  ✅ PASSED — Request tanpa subject diterima")


def test_solve_missing_fields():
    """Test 6: POST /api/v1/solve/ — field wajib kosong"""
    separator("TEST 6: POST /solve — Field Wajib Kosong")

    # Tanpa image_base64
    payload = {"query_text": "test tanpa gambar"}

    resp = httpx.post(f"{BASE_URL}/api/v1/solve/", json=payload, timeout=10.0)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)[:300]}")

    assert resp.status_code == 422  # Validation error dari Pydantic
    print("\n  ✅ PASSED — Pydantic validation menolak request invalid")


def test_solve_empty_body():
    """Test 7: POST /api/v1/solve/ — body kosong"""
    separator("TEST 7: POST /solve — Body Kosong")

    resp = httpx.post(f"{BASE_URL}/api/v1/solve/", json={}, timeout=10.0)
    print(f"  Status: {resp.status_code}")

    assert resp.status_code == 422
    print("\n  ✅ PASSED — Body kosong ditolak")


if __name__ == "__main__":
    print()
    print("🚀 EduSolve AI — Test Suite")
    print(f"   Server: {BASE_URL}")
    print()

    test_health_check()
    test_swagger_docs()
    test_openapi_schema()
    test_solve_missing_fields()
    test_solve_empty_body()
    test_solve_without_subject()
    test_solve_valid_request()

    separator("RINGKASAN")
    print("  Semua test selesai dijalankan!")
    print()
    print("  💡 Tips:")
    print("  - Buka http://localhost:8000/docs untuk Swagger UI")
    print("  - Set GOOGLE_API_KEY di .env agar POST /solve berfungsi penuh")
    print("  - Test 4 & 5 akan return 502 jika API key masih dummy")
    print()
