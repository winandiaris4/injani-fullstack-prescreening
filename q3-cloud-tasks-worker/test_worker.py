"""
Q3 — Cloud Tasks Worker Tests
Tests untuk memverifikasi HTTP worker endpoint bekerja sesuai spesifikasi Cloud Tasks.

Strategi: Inject header Cloud Tasks secara manual ke FastAPI TestClient
(tidak butuh GCP atau emulator running).
"""

import pytest
from fastapi.testclient import TestClient

from worker import app, processed_tasks, dead_letter_queue


@pytest.fixture(autouse=True)
def clear_state():
    """Reset in-memory state before each test."""
    processed_tasks.clear()
    dead_letter_queue.clear()
    yield
    processed_tasks.clear()
    dead_letter_queue.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ─── Header Validation Tests ──────────────────────────────────────────────────

class TestHeaderValidation:

    def test_missing_task_name_returns_400(self, client):
        """Cloud Tasks selalu mengirim X-CloudTasks-TaskName. Jika tidak ada → 400."""
        response = client.post(
            "/tasks/process",
            json={"task_type": "test"},
            # No X-CloudTasks-TaskName header
        )
        assert response.status_code == 400
        assert "X-CloudTasks-TaskName" in response.json()["detail"]

    def test_valid_cloud_tasks_headers_accepted(self, client):
        """Request dengan header Cloud Tasks valid harus diterima dan diproses."""
        response = client.post(
            "/tasks/process",
            headers={
                "X-CloudTasks-TaskName": "projects/p/locations/l/queues/q/tasks/task-001",
                "X-CloudTasks-QueueName": "injani-queue",
                "X-CloudTasks-TaskRetryCount": "0",
            },
            json={"task_type": "nightly_report", "target_date": "2026-09-11"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "task_name" in data


# ─── Normal Processing Tests ──────────────────────────────────────────────────

class TestNormalProcessing:

    def test_task_processed_successfully(self, client):
        response = client.post(
            "/tasks/process",
            headers={
                "X-CloudTasks-TaskName": "projects/p/locations/l/queues/q/tasks/report-001",
                "X-CloudTasks-QueueName": "injani-queue",
                "X-CloudTasks-TaskRetryCount": "0",
            },
            json={"task_type": "generate_pdf"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_processed_task_stored_in_memory(self, client):
        task_name = "projects/p/locations/l/queues/q/tasks/task-store-test"
        client.post(
            "/tasks/process",
            headers={
                "X-CloudTasks-TaskName": task_name,
                "X-CloudTasks-QueueName": "injani-queue",
                "X-CloudTasks-TaskRetryCount": "0",
            },
            json={"task_type": "test"},
        )
        assert task_name in processed_tasks


# ─── Idempotency Tests ────────────────────────────────────────────────────────

class TestIdempotency:

    def test_duplicate_task_skipped(self, client):
        """
        Cloud Tasks bisa mengirim task yang sama lebih dari sekali (at-least-once delivery).
        Worker harus mendeteksi duplikat dan skip tanpa error.
        """
        headers = {
            "X-CloudTasks-TaskName": "projects/p/locations/l/queues/q/tasks/idempotent-001",
            "X-CloudTasks-QueueName": "injani-queue",
            "X-CloudTasks-TaskRetryCount": "0",
        }
        payload = {"task_type": "send_email"}

        # First request — should process
        r1 = client.post("/tasks/process", headers=headers, json=payload)
        assert r1.status_code == 200
        assert r1.json()["status"] == "success"

        # Second request with same task name — should skip
        r2 = client.post("/tasks/process", headers=headers, json=payload)
        assert r2.status_code == 200
        assert r2.json()["status"] == "already_processed"

        # Only one entry in processed_tasks
        assert len(processed_tasks) == 1


# ─── Retry & Dead Letter Tests ────────────────────────────────────────────────

class TestRetryAndDeadLetter:

    def test_force_fail_returns_500(self, client):
        """
        Jika payload mengandung force_fail=true, worker mengembalikan 500.
        Ini mensimulasikan task failure yang akan di-retry oleh Cloud Tasks.
        """
        response = client.post(
            "/tasks/process",
            headers={
                "X-CloudTasks-TaskName": "projects/p/locations/l/queues/q/tasks/fail-001",
                "X-CloudTasks-QueueName": "injani-queue",
                "X-CloudTasks-TaskRetryCount": "1",
            },
            json={"task_type": "test", "force_fail": True},
        )
        assert response.status_code == 500
        assert response.json()["status"] == "failed"

    def test_dead_letter_after_max_retries(self, client):
        """
        Setelah 5 retry, task harus dipindahkan ke Dead Letter Queue.
        Worker mengembalikan 200 (bukan 5xx) agar Cloud Tasks berhenti retry.
        """
        response = client.post(
            "/tasks/process",
            headers={
                "X-CloudTasks-TaskName": "projects/p/locations/l/queues/q/tasks/dlq-001",
                "X-CloudTasks-QueueName": "injani-queue",
                "X-CloudTasks-TaskRetryCount": "5",  # >= max_retries
            },
            json={"task_type": "test"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "dead_lettered"
        assert len(dead_letter_queue) == 1
        assert dead_letter_queue[0]["reason"] == "max_retries_exceeded"

    def test_retry_before_max_still_fails(self, client):
        """Retry ke-3 dengan force_fail masih mengembalikan 500 (belum dead-letter)."""
        response = client.post(
            "/tasks/process",
            headers={
                "X-CloudTasks-TaskName": "projects/p/locations/l/queues/q/tasks/retry-003",
                "X-CloudTasks-QueueName": "injani-queue",
                "X-CloudTasks-TaskRetryCount": "3",
            },
            json={"task_type": "test", "force_fail": True},
        )
        assert response.status_code == 500
        assert len(dead_letter_queue) == 0  # Belum masuk DLQ


# ─── Inspection Endpoints ─────────────────────────────────────────────────────

class TestInspectionEndpoints:

    def test_dead_letter_endpoint(self, client):
        response = client.get("/tasks/dead-letter")
        assert response.status_code == 200
        assert "count" in response.json()

    def test_processed_endpoint(self, client):
        response = client.get("/tasks/processed")
        assert response.status_code == 200
        assert "count" in response.json()

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

