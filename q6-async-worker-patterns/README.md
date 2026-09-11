# Q6 — Python Async Workers & Background Job Patterns

PoC untuk menjawab **Question 6** dari pre-screening INJANI SYSTEMS.

## Overview

Demonstrasi 3 pola async worker di FastAPI:

| Pattern | Use Case | Infrastruktur |
|---|---|---|
| `BackgroundTasks` | Fire-and-forget ringan (< 1 detik) | Tidak ada |
| `ARQ` (async Redis Queue) | Task 1–5 menit, persistent | Redis |
| Idempotency Key | Mencegah duplikasi saat retry | Redis (fakeredis untuk testing) |

## Cara Menjalankan

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run tests
```bash
pytest test_idempotency.py -v
```

### 3. Jalankan server
```bash
uvicorn app:app --reload --port 8002
```

### 4. Test endpoints

#### Buat task (return 202 Accepted)
```bash
curl -X POST http://localhost:8002/tasks/start \
  -H "Content-Type: application/json" \
  -d '{"duration": 5}'
# Response: {"task_id": "abc-123", "status": "QUEUED"}
```

#### Cek status (polling)
```bash
curl http://localhost:8002/tasks/abc-123/status
# Response: {"task_id": "abc-123", "status": "RUNNING", "percent": 60}
```

#### Stream progress (SSE)
```bash
curl -N http://localhost:8002/tasks/abc-123/sse
# Streams: data: {"task_id": "abc-123", "status": "RUNNING", "percent": 40}
```

## Idempotency Pattern

```
Client ──[POST /tasks/start]──► FastAPI
            + Header: Idempotency-Key: abc-uuid-123
                │
                ▼
         Redis SET "idempotency:lock:abc-uuid-123" NX EX 86400
                │
         ┌──── Lock acquired? ────┐
         │ YES (new request)      │ NO (duplicate)
         ▼                        ▼
    Generate new task_id    Return existing task_id
    Store ref in Redis      Status: "ALREADY_PROCESSING"
    Enqueue ARQ job
```

## Perbandingan Pattern

| Solusi | Kelebihan | Kekurangan | Kapan Dipilih |
|---|---|---|---|
| **BackgroundTasks** | Tanpa dependensi | Task hilang saat restart | Task < 1 detik (kirim email) |
| **ARQ** | Native asyncio, ringan | Butuh Redis | Task 1–5 menit di FastAPI |
| **Celery** | Fitur lengkap | Rumit, overhead tinggi | Monolith skala besar |
| **Cloud Tasks HTTP** | Serverless, auto-retry | GCP vendor lock-in | Task berat di GCP |

