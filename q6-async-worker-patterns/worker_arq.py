"""
Q6 — ARQ Worker Implementation
ARQ adalah async Redis queue yang native asyncio, ideal untuk FastAPI.

Dibandingkan Celery:
  - Lebih ringan (tidak butuh komplit broker setup)
  - Native asyncio (tidak ada thread pool overhead)
  - Cocok untuk task 1–5 menit

Cara menjalankan worker (butuh Redis):
    arq worker_arq.WorkerSettings

Atau dengan fakeredis untuk testing:
    (dihandle di test_idempotency.py)
"""

import asyncio
import json
from typing import Any


# ─── ARQ Task Functions ───────────────────────────────────────────────────────

async def generate_pdf_report(ctx: dict, report_id: str, target_date: str) -> dict:
    """
    ARQ task: simulates PDF report generation.

    Args:
        ctx: ARQ context (contains 'redis' for progress updates)
        report_id: Unique report identifier
        target_date: Date range for the report

    Returns:
        dict with generation result
    """
    redis = ctx.get("redis")
    steps = [
        ("FETCHING_DATA", 20),
        ("PROCESSING", 40),
        ("GENERATING_PDF", 70),
        ("UPLOADING", 90),
        ("DONE", 100),
    ]

    for status, percent in steps:
        await asyncio.sleep(0.1)  # Simulate work (reduced for testing speed)
        progress = {"status": status, "percent": percent}

        if redis:
            await redis.set(
                f"task_progress:{report_id}",
                json.dumps(progress),
                ex=3600,
            )

    return {
        "report_id": report_id,
        "target_date": target_date,
        "file_url": f"gs://injani-reports/{report_id}.pdf",
        "status": "DONE",
    }


async def send_email_notification(ctx: dict, recipient: str, subject: str, body: str) -> dict:
    """
    ARQ task: simulates sending an email notification.
    Simple, fast task — suitable for BackgroundTasks too.
    """
    await asyncio.sleep(0.05)  # Simulate SMTP call
    return {
        "status": "sent",
        "recipient": recipient,
        "subject": subject,
    }


# ─── ARQ Worker Settings ──────────────────────────────────────────────────────

class WorkerSettings:
    """
    ARQ worker configuration.
    Replace RedisSettings with actual Redis connection in production.
    """
    functions = [generate_pdf_report, send_email_notification]
    max_jobs = 10
    job_timeout = 300  # 5 minutes

    # For production:
    # from arq.connections import RedisSettings
    # redis_settings = RedisSettings(host='redis-host', port=6379)

