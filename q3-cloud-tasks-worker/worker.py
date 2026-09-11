"""
Q3 — Cloud Tasks HTTP Worker
FastAPI endpoint yang mensimulasikan Cloud Tasks HTTP worker.

Endpoint: POST /tasks/process
- Membaca dan memvalidasi header Cloud Tasks
- Memproses payload task
- Mengembalikan 2xx untuk sukses, 5xx untuk retry
"""

import json
import logging
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Injani Cloud Tasks Worker", version="1.0.0")

# ─── Simulated task storage (in-memory for PoC) ───────────────────────────────
processed_tasks: dict[str, Any] = {}
dead_letter_queue: list[dict] = []


@app.post("/tasks/process")
async def process_task(
    request: Request,
    x_cloudtasks_taskname: str | None = Header(default=None),
    x_cloudtasks_queuename: str | None = Header(default=None),
    x_cloudtasks_taskretrycount: int | None = Header(default=0),
    x_cloudtasks_tasketa: str | None = Header(default=None),
) -> JSONResponse:
    """
    Cloud Tasks HTTP worker endpoint.

    Cloud Tasks akan mengirim request ke sini dengan header:
      X-CloudTasks-TaskName    : Nama unik task
      X-CloudTasks-QueueName   : Nama queue
      X-CloudTasks-TaskRetryCount : Jumlah retry yang sudah terjadi
      X-CloudTasks-TaskETA     : Scheduled execution time

    Worker harus mengembalikan 2xx agar Cloud Tasks menandai task sebagai sukses.
    Jika mengembalikan 5xx, Cloud Tasks akan melakukan retry dengan exponential backoff.
    """

    # ── Validasi header mandatory ──────────────────────────────────────────────
    if not x_cloudtasks_taskname:
        raise HTTPException(
            status_code=400,
            detail="Missing required header: X-CloudTasks-TaskName",
        )

    task_name = x_cloudtasks_taskname
    queue_name = x_cloudtasks_queuename or "default"
    retry_count = x_cloudtasks_taskretrycount or 0

    # ── Cek apakah task sudah diproses (idempotency) ──────────────────────────
    if task_name in processed_tasks:
        logger.info("Task %s already processed (idempotent skip)", task_name)
        return JSONResponse(
            content={
                "status": "already_processed",
                "task_name": task_name,
                "message": "Task was already completed — idempotent skip.",
            }
        )

    # ── Baca payload ──────────────────────────────────────────────────────────
    try:
        body = await request.json()
    except Exception:
        body = {}

    logger.info(
        "Processing task",
        extra={
            "task_name": task_name,
            "queue_name": queue_name,
            "retry_count": retry_count,
            "payload": body,
        },
    )

    # ── Simulasi Dead Letter: jika retry sudah >= 5 ───────────────────────────
    max_retries = 5
    if retry_count >= max_retries:
        dead_letter_queue.append({
            "task_name": task_name,
            "queue_name": queue_name,
            "retry_count": retry_count,
            "payload": body,
            "reason": "max_retries_exceeded",
        })
        logger.error("Task %s moved to Dead Letter Queue after %d retries", task_name, retry_count)
        # Tetap return 200 agar Cloud Tasks berhenti mencoba (DLQ sudah ditangani)
        return JSONResponse(
            status_code=200,
            content={
                "status": "dead_lettered",
                "task_name": task_name,
                "message": f"Task moved to Dead Letter Queue after {retry_count} retries.",
            },
        )

    # ── Simulasi task failure jika payload mengandung 'force_fail': true ──────
    if body.get("force_fail"):
        logger.warning("Task %s forced to fail (retry_count=%d)", task_name, retry_count)
        return JSONResponse(
            status_code=500,
            content={
                "status": "failed",
                "task_name": task_name,
                "message": "Simulated failure — Cloud Tasks will retry with backoff.",
            },
        )

    # ── Proses task berhasil ──────────────────────────────────────────────────
    result = {
        "task_type": body.get("task_type", "generic"),
        "processed_at": "2026-09-11T00:00:00Z",
        "payload_keys": list(body.keys()),
    }

    processed_tasks[task_name] = result
    logger.info("Task %s processed successfully", task_name)

    return JSONResponse(
        content={
            "status": "success",
            "task_name": task_name,
            "queue": queue_name,
            "result": result,
        }
    )


@app.get("/tasks/dead-letter")
async def get_dead_letter_queue() -> JSONResponse:
    """Inspect tasks that exceeded max retries."""
    return JSONResponse(content={"count": len(dead_letter_queue), "tasks": dead_letter_queue})


@app.get("/tasks/processed")
async def get_processed_tasks() -> JSONResponse:
    """Inspect successfully processed tasks."""
    return JSONResponse(content={"count": len(processed_tasks), "tasks": processed_tasks})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

