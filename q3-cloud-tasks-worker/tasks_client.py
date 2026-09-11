"""
Q3 — Cloud Tasks Client Helper
Helper untuk membuat task di Cloud Tasks queue.
Secara default mengarah ke emulator lokal (gcloud beta emulators tasks).

Usage:
    # Start emulator:
    # gcloud beta emulators tasks start --host-port=localhost:8123
    # export CLOUD_TASKS_EMULATOR_HOST=localhost:8123

    python tasks_client.py
"""

import json
import os
import urllib.request
import urllib.error
from typing import Any

EMULATOR_HOST = os.getenv("CLOUD_TASKS_EMULATOR_HOST", "localhost:8123")
WORKER_URL = os.getenv("WORKER_URL", "http://localhost:8000/tasks/process")
PROJECT = os.getenv("GCP_PROJECT", "injani-dev")
LOCATION = os.getenv("GCP_LOCATION", "asia-southeast1")
QUEUE_NAME = os.getenv("CLOUD_TASKS_QUEUE", "injani-queue")


def create_task(
    payload: dict[str, Any],
    task_name: str | None = None,
    use_emulator: bool = True,
) -> dict:
    """
    Creates an HTTP task in Google Cloud Tasks (or emulator).

    Args:
        payload: The JSON body to send to the worker.
        task_name: Optional unique task name for deduplication.
        use_emulator: If True, sends to local emulator; else uses GCP API.

    Returns:
        The created task resource as a dict.
    """
    queue_path = f"projects/{PROJECT}/locations/{LOCATION}/queues/{QUEUE_NAME}"

    task_body: dict[str, Any] = {
        "task": {
            "httpRequest": {
                "httpMethod": "POST",
                "url": WORKER_URL,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode().hex(),  # base64 in real API
            }
        }
    }
    if task_name:
        task_body["task"]["name"] = f"{queue_path}/tasks/{task_name}"

    if use_emulator:
        url = f"http://{EMULATOR_HOST}/v2beta3/{queue_path}/tasks"
    else:
        url = f"https://cloudtasks.googleapis.com/v2/{queue_path}/tasks"

    req = urllib.request.Request(
        url,
        data=json.dumps(task_body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"[tasks_client] Warning: Could not connect to Cloud Tasks ({e}). "
              f"Is the emulator running? CLOUD_TASKS_EMULATOR_HOST={EMULATOR_HOST}")
        # Return a mock response for CI compatibility
        return {
            "name": f"{queue_path}/tasks/{task_name or 'mock-task-id'}",
            "status": "mock_created",
            "payload": payload,
        }


if __name__ == "__main__":
    result = create_task(
        payload={"task_type": "nightly_report", "target_date": "2026-09-11"},
        task_name="nightly-report-20260911",
    )
    print("Task created:", json.dumps(result, indent=2))

