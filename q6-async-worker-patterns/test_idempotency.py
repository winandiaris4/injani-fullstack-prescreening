"""
Q6 — Idempotency Tests
Membuktikan bahwa request kedua dengan Idempotency-Key yang sama
mengembalikan task_id yang sama tanpa trigger eksekusi ulang.

Menggunakan fakeredis — tidak butuh Redis real.
"""

import uuid

import fakeredis
from fastapi.testclient import TestClient
import pytest

from app import app
from idempotency import get_task_ref, reset_redis, start_task_with_idempotency
from worker_arq import generate_pdf_report, send_email_notification


@pytest.fixture(autouse=True)
def clear_redis():
    """Reset fakeredis state before each test."""
    reset_redis()
    yield
    reset_redis()


@pytest.fixture
def redis_client():
    """Provide a fresh isolated fakeredis instance for tests that need isolation."""
    return fakeredis.FakeRedis(decode_responses=True)


# ─── Core Idempotency Tests ───────────────────────────────────────────────────

class TestIdempotencyCore:

    def test_first_request_creates_new_task(self, redis_client):
        """First request with a new key should create a task and return is_new=True."""
        key = str(uuid.uuid4())
        task_id, is_new = start_task_with_idempotency(key, {"type": "report"}, redis_client)

        assert is_new is True
        assert isinstance(task_id, str)
        assert len(task_id) == 36  # UUID format

    def test_second_request_returns_same_task_id(self, redis_client):
        """Second request with same key must return the same task_id, is_new=False."""
        key = str(uuid.uuid4())
        payload = {"type": "pdf_generation", "target_date": "2026-09-11"}

        task_id_1, is_new_1 = start_task_with_idempotency(key, payload, redis_client)
        task_id_2, is_new_2 = start_task_with_idempotency(key, payload, redis_client)

        assert is_new_1 is True
        assert is_new_2 is False
        assert task_id_1 == task_id_2, (
            f"Expected same task_id but got:\n  1st: {task_id_1}\n  2nd: {task_id_2}"
        )

    def test_different_keys_create_different_tasks(self, redis_client):
        """Different idempotency keys must produce different task IDs."""
        key_a = str(uuid.uuid4())
        key_b = str(uuid.uuid4())

        task_id_a, _ = start_task_with_idempotency(key_a, {"type": "task_a"}, redis_client)
        task_id_b, _ = start_task_with_idempotency(key_b, {"type": "task_b"}, redis_client)

        assert task_id_a != task_id_b

    def test_many_duplicate_requests_return_same_id(self, redis_client):
        """10 concurrent-simulated requests with same key return the same task_id."""
        key = str(uuid.uuid4())
        results = []

        for _ in range(10):
            task_id, is_new = start_task_with_idempotency(key, {"type": "report"}, redis_client)
            results.append((task_id, is_new))

        # Only the first should be new
        assert results[0][1] is True
        for task_id, is_new in results[1:]:
            assert is_new is False
            assert task_id == results[0][0]

    def test_task_ref_is_retrievable(self, redis_client):
        """task_id associated with an idempotency key should be retrievable."""
        key = str(uuid.uuid4())
        task_id, _ = start_task_with_idempotency(key, {}, redis_client)

        ref = get_task_ref(key, redis_client)
        assert ref == task_id


# ─── FastAPI Integration Tests ────────────────────────────────────────────────

class TestFastAPIWorkflow:
    """
    Integration tests for the FastAPI async task endpoints.
    """

    def test_start_task_returns_202(self):
        client = TestClient(app)
        response = client.post("/tasks/start", json={"duration": 0.1})
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "QUEUED"

    def test_task_status_endpoint_returns_task(self):
        client = TestClient(app)
        # Create task
        create_resp = client.post("/tasks/start", json={"duration": 0.1})
        task_id = create_resp.json()["task_id"]

        # Check status
        status_resp = client.get(f"/tasks/{task_id}/status")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["task_id"] == task_id
        assert data["status"] in ("QUEUED", "RUNNING", "DONE")

    def test_unknown_task_status_returns_404(self):
        client = TestClient(app)
        response = client.get("/tasks/non-existent-task-id/status")
        assert response.status_code == 404

    def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# ─── ARQ Worker Tests ─────────────────────────────────────────────────────────

class TestARQWorker:

    @pytest.mark.asyncio
    async def test_generate_pdf_report_completes(self):
        """ARQ task function should complete and return expected result."""
        ctx: dict = {}  # No Redis in this unit test
        result = await generate_pdf_report(ctx, "report-001", "2026-09-11")

        assert result["status"] == "DONE"
        assert result["report_id"] == "report-001"
        assert "file_url" in result

    @pytest.mark.asyncio
    async def test_send_email_completes(self):
        """Email notification task should complete successfully."""
        ctx: dict = {}
        result = await send_email_notification(
            ctx,
            recipient="aris@example.com",
            subject="Report Ready",
            body="Your report is ready.",
        )
        assert result["status"] == "sent"
        assert result["recipient"] == "aris@example.com"

