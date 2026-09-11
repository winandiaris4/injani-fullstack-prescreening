"""
Q6 — Idempotency Key Middleware
Mencegah eksekusi ganda menggunakan Redis SET NX (atomic lock).

Pattern:
  1. Client menyertakan header: Idempotency-Key: <unique-uuid>
  2. Handler mencek Redis secara atomik (SET ... NX EX)
  3. Jika key sudah ada → kembalikan task_id yang sama tanpa trigger baru
  4. Jika key baru → simpan lock + jalankan task

Menggunakan fakeredis untuk testing tanpa Redis real.
"""

import uuid
from typing import Any

import fakeredis


# ─── Redis client (fakeredis untuk PoC, ganti dengan redis.asyncio di produksi) ──

def get_redis() -> fakeredis.FakeRedis:
    """Returns a shared fakeredis instance (simulates real Redis)."""
    return _SHARED_REDIS


_SHARED_REDIS = fakeredis.FakeRedis(decode_responses=True)


# ─── Idempotency Logic ────────────────────────────────────────────────────────

IDEMPOTENCY_TTL_SECONDS = 86_400  # 24 jam


def start_task_with_idempotency(
    idempotency_key: str,
    task_payload: dict[str, Any],
    redis: fakeredis.FakeRedis | None = None,
) -> tuple[str, bool]:
    """
    Starts a task only if the idempotency_key has not been seen before.

    Uses Redis SET NX (set-if-not-exists) for atomic lock acquisition.

    Args:
        idempotency_key: Unique identifier supplied by the client (UUID).
        task_payload: The task parameters.
        redis: Redis client (defaults to shared fakeredis instance).

    Returns:
        (task_id, is_new): task_id is the ID of the task (new or existing),
                           is_new indicates whether the task was actually started.
    """
    r = redis or _SHARED_REDIS
    lock_key = f"idempotency:lock:{idempotency_key}"
    ref_key = f"idempotency:task_ref:{idempotency_key}"

    # Atomic: SET lock_key "LOCKED" NX EX ttl
    # Returns True if key was newly set (we won the lock), False if already existed
    acquired = r.set(lock_key, "LOCKED", nx=True, ex=IDEMPOTENCY_TTL_SECONDS)

    if not acquired:
        # Key already exists → duplicate request
        existing_task_id = r.get(ref_key)
        if existing_task_id:
            return existing_task_id, False
        # Fallback if ref somehow missing
        return "unknown", False

    # New request: generate task ID and store reference
    task_id = str(uuid.uuid4())
    r.set(ref_key, task_id, ex=IDEMPOTENCY_TTL_SECONDS)

    # In production: enqueue the actual task here
    # await arq_pool.enqueue_job("generate_pdf_report", task_id, **task_payload)

    return task_id, True


def get_task_ref(idempotency_key: str, redis: fakeredis.FakeRedis | None = None) -> str | None:
    """Look up the task_id associated with an idempotency key."""
    r = redis or _SHARED_REDIS
    return r.get(f"idempotency:task_ref:{idempotency_key}")


def reset_redis() -> None:
    """Helper for tests: clear all keys from the shared fakeredis instance."""
    _SHARED_REDIS.flushall()

