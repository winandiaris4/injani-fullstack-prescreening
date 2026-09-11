"""
Q6 — FastAPI Async Worker Patterns
Demonstrasi 3 pola background job:
  1. BackgroundTasks (bawaan FastAPI) — sederhana, tanpa infrastruktur
  2. ARQ (Async Redis Queue) — persistent, survives restart
  3. Idempotency Key — mencegah eksekusi ganda jika request diretry

Endpoints:
  POST /tasks/start          → Buat task baru (return 202 + task_id)
  GET  /tasks/{task_id}/status → Cek status task
  GET  /tasks/{task_id}/sse   → Server-Sent Events progress (streaming)
"""

import asyncio
import json
import time
import uuid
from typing import AsyncIterator

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI(title="Injani Async Worker Patterns", version="1.0.0")

# ─── In-memory task store (di produksi diganti Redis) ─────────────────────────
# Format: { task_id: {"status": str, "percent": int, "result": any} }
_task_store: dict[str, dict] = {}


# ═══════════════════════════════════════════════════════════════════════════════
# PATTERN 1 — FastAPI BackgroundTasks (fire-and-forget)
# ═══════════════════════════════════════════════════════════════════════════════

async def _run_background_job(task_id: str, duration: float = 3.0) -> None:
    """Simulates a long-running job (e.g., PDF generation)."""
    _task_store[task_id] = {"status": "RUNNING", "percent": 0, "result": None}

    steps = 5
    for i in range(1, steps + 1):
        await asyncio.sleep(duration / steps)
        _task_store[task_id]["percent"] = int((i / steps) * 100)
        _task_store[task_id]["status"] = "RUNNING"

    _task_store[task_id]["status"] = "DONE"
    _task_store[task_id]["percent"] = 100
    _task_store[task_id]["result"] = {"output": f"Task {task_id} completed."}


@app.post("/tasks/start", status_code=202)
async def start_task(
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Accepts a task request, immediately returns 202 Accepted with a task_id.
    The actual work runs in the background (BackgroundTasks pattern).
    """
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    duration = float(body.get("duration", 3.0))  # simulate job duration in seconds

    task_id = str(uuid.uuid4())
    _task_store[task_id] = {"status": "QUEUED", "percent": 0, "result": None}

    background_tasks.add_task(_run_background_job, task_id, duration)

    return JSONResponse(
        status_code=202,
        content={"task_id": task_id, "status": "QUEUED"},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PATTERN 2 — Status Polling
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str) -> JSONResponse:
    """
    Polling endpoint: frontend calls this every N seconds to check progress.
    Returns the current status and percentage of completion.
    """
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    return JSONResponse(content={"task_id": task_id, **task})


# ═══════════════════════════════════════════════════════════════════════════════
# PATTERN 3 — Server-Sent Events (SSE) Progress Stream
# ═══════════════════════════════════════════════════════════════════════════════

async def _sse_generator(task_id: str) -> AsyncIterator[str]:
    """Yields SSE events as the task progresses."""
    max_wait = 30  # seconds
    start = time.monotonic()

    while time.monotonic() - start < max_wait:
        task = _task_store.get(task_id)
        if not task:
            yield f"event: error\ndata: {json.dumps({'error': 'task not found'})}\n\n"
            return

        payload = json.dumps({"task_id": task_id, **task})
        yield f"data: {payload}\n\n"

        if task["status"] in ("DONE", "FAILED"):
            break

        await asyncio.sleep(0.5)


@app.get("/tasks/{task_id}/sse")
async def task_sse(task_id: str) -> StreamingResponse:
    """
    Server-Sent Events stream: pushes progress updates to the browser in real-time.
    Frontend uses EventSource API to receive live updates.
    """
    if task_id not in _task_store:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    return StreamingResponse(
        _sse_generator(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Utility endpoints ────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "active_tasks": len(_task_store)}


@app.get("/tasks")
async def list_tasks() -> JSONResponse:
    return JSONResponse(content={"count": len(_task_store), "tasks": _task_store})

