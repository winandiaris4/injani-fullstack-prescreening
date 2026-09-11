# Q3 — Cloud Tasks Testing & Monitoring Worker

PoC untuk menjawab **Question 3** dari pre-screening INJANI SYSTEMS.

## Overview

FastAPI HTTP worker yang mensimulasikan integrasi dengan Google Cloud Tasks:
- Memvalidasi header identitas Cloud Tasks
- Menangani idempotency (duplicate delivery)
- Mensimulasikan retry logic dan Dead Letter Queue

## Cara Menjalankan

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Jalankan tests
```bash
pytest test_worker.py -v
```

### 3. Jalankan worker server
```bash
uvicorn worker:app --reload --port 8001
```

### 4. Simulasi Cloud Tasks request
```bash
# Request normal
curl -X POST http://localhost:8001/tasks/process \
  -H "X-CloudTasks-TaskName: projects/my-project/locations/asia-southeast1/queues/injani-queue/tasks/task-001" \
  -H "X-CloudTasks-QueueName: injani-queue" \
  -H "X-CloudTasks-TaskRetryCount: 0" \
  -H "Content-Type: application/json" \
  -d '{"task_type": "nightly_report", "target_date": "2026-09-11"}'

# Simulasi failure (akan di-retry oleh Cloud Tasks)
curl -X POST http://localhost:8001/tasks/process \
  -H "X-CloudTasks-TaskName: projects/my-project/locations/asia-southeast1/queues/injani-queue/tasks/task-fail-001" \
  -H "X-CloudTasks-TaskRetryCount: 1" \
  -H "Content-Type: application/json" \
  -d '{"task_type": "test", "force_fail": true}'
```

## Testing dengan Cloud Tasks Emulator (Lokal)

```bash
# Install dan jalankan emulator
gcloud beta emulators tasks start --host-port=localhost:8123
export CLOUD_TASKS_EMULATOR_HOST=localhost:8123

# Buat task via client helper
python tasks_client.py
```

## Header Cloud Tasks yang Divalidasi

| Header | Keterangan |
|---|---|
| `X-CloudTasks-TaskName` | Nama unik task (mandatory) |
| `X-CloudTasks-QueueName` | Nama queue asal |
| `X-CloudTasks-TaskRetryCount` | Jumlah retry yang sudah terjadi |
| `X-CloudTasks-TaskETA` | Scheduled execution time |

## Behavior

| Kondisi | Response | Keterangan |
|---|---|---|
| Normal request | `200 success` | Task diproses dan disimpan |
| Duplicate task name | `200 already_processed` | Idempotent skip |
| `force_fail: true` + retry < 5 | `500 failed` | Cloud Tasks akan retry |
| `retry_count >= 5` | `200 dead_lettered` | Task pindah ke DLQ |

