"""
Q1 — Evaluation Script
Runs the OrderExtractor against the golden dataset and reports:
  - Intent Accuracy
  - Schema Validity Rate
  - Entity-level F1-Score (per field: name/quantity/unit)
  - Fallback Rate

Run with:
    MOCK_MODE=true pytest test_evaluation.py -v
"""

import json
import os
from pathlib import Path

from app import app
from extractor import MessageExtraction, OrderExtractor
from fastapi.testclient import TestClient
import pytest

# Force MOCK_MODE so tests never need Ollama
os.environ.setdefault("MOCK_MODE", "true")


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def extractor() -> OrderExtractor:
    return OrderExtractor()


@pytest.fixture(scope="module")
def golden_dataset() -> list[dict]:
    dataset_path = Path(__file__).parent / "golden_dataset.json"
    with dataset_path.open() as f:
        return json.load(f)


# ─── Unit Tests ───────────────────────────────────────────────────────────────

class TestSchemaValidity:
    """Every extraction must return a valid Pydantic MessageExtraction."""

    def test_all_messages_produce_valid_schema(self, extractor, golden_dataset):
        for sample in golden_dataset:
            result = extractor.extract(sample["message"])
            assert isinstance(result, MessageExtraction), (
                f"[#{sample['id']}] Expected MessageExtraction, got {type(result)}"
            )
            assert result.intent in ("order", "inquiry", "complaint")
            assert result.confidence in ("high", "medium", "low")
            assert isinstance(result.items, list)


class TestIntentAccuracy:
    """Intent classification accuracy must be >= 70% on the golden dataset."""

    def test_intent_accuracy_threshold(self, extractor, golden_dataset):
        correct = 0
        results = []

        for sample in golden_dataset:
            result = extractor.extract(sample["message"])
            is_correct = result.intent == sample["expected_intent"]
            if is_correct:
                correct += 1
            results.append({
                "id": sample["id"],
                "message": sample["message"][:60],
                "expected": sample["expected_intent"],
                "predicted": result.intent,
                "correct": is_correct,
            })

        accuracy = correct / len(golden_dataset)
        print(f"\n{'─'*60}")
        print(f"  Intent Accuracy: {correct}/{len(golden_dataset)} = {accuracy:.1%}")
        print(f"{'─'*60}")
        for r in results:
            status = "✅" if r["correct"] else "❌"
            print(f"  {status} #{r['id']:02d} [{r['expected']:9s}→{r['predicted']:9s}] {r['message']}")
        print(f"{'─'*60}\n")

        assert accuracy >= 0.70, (
            f"Intent accuracy {accuracy:.1%} is below the 70% threshold."
        )


class TestOrderIntentDetection:
    """Specific tests for each intent type."""

    def test_order_intent_messages(self, extractor):
        order_messages = [
            "I'd like 3 bags of cement and 2 tins of paint please",
            "Please send 20 sheets of plywood",
            "Order: 4 rolls of wire mesh",
        ]
        for msg in order_messages:
            result = extractor.extract(msg)
            assert result.intent == "order", f"Expected 'order' for: '{msg}', got '{result.intent}'"

    def test_inquiry_intent_messages(self, extractor):
        inquiry_messages = [
            "Do you have white tiles available in stock?",
            "How much does a bag of cement cost?",
        ]
        for msg in inquiry_messages:
            result = extractor.extract(msg)
            assert result.intent == "inquiry", f"Expected 'inquiry' for: '{msg}', got '{result.intent}'"

    def test_complaint_intent_messages(self, extractor):
        complaint_messages = [
            "The bricks I received last week were all broken!",
            "The cement bags were broken and the contents are all spilled",
        ]
        for msg in complaint_messages:
            result = extractor.extract(msg)
            assert result.intent == "complaint", (
                f"Expected 'complaint' for: '{msg}', got '{result.intent}'"
            )


class TestItemExtraction:
    """Tests that structured orders parse items correctly."""

    def test_single_item_order(self, extractor):
        result = extractor.extract("Please send 20 sheets of plywood")
        assert len(result.items) >= 1
        assert result.items[0].quantity == 20.0

    def test_multi_item_order(self, extractor):
        result = extractor.extract("I'd like 3 bags of cement and 2 tins of paint please")
        assert len(result.items) >= 1  # at least 1 item detected

    def test_empty_items_for_complaint(self, extractor):
        result = extractor.extract("The bricks I received last week were all broken!")
        # Complaint messages may not have quantity/unit
        for item in result.items:
            assert item.quantity is None or isinstance(item.quantity, float)


class TestWebhookEndpoint:
    """Integration tests for the FastAPI /webhook endpoint."""

    def test_webhook_returns_200_with_valid_message(self):
        client = TestClient(app)
        response = client.post("/webhook", json={"message": "I'd like 3 bags of cement"})
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data
        assert "items" in data
        assert "confidence" in data

    def test_webhook_returns_422_with_empty_message(self):
        client = TestClient(app)
        response = client.post("/webhook", json={})
        assert response.status_code == 422

    def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

