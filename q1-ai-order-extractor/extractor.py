"""
Q1 — OrderExtractor
Handles LLM-based (or mock) extraction of order intent from raw WhatsApp messages.

Supports two modes:
  - MOCK_MODE=true  → Uses rule-based mock logic (no Ollama/GPU needed)
  - MOCK_MODE=false → Calls Ollama HTTP API (requires running Ollama server)
"""

import json
import os
import re
import urllib.request
import urllib.error
from typing import Literal

from pydantic import BaseModel


# ─── Pydantic Output Schema ───────────────────────────────────────────────────

class OrderItem(BaseModel):
    name: str
    quantity: float | None = None
    unit: str | None = None


class MessageExtraction(BaseModel):
    items: list[OrderItem]
    intent: Literal["order", "inquiry", "complaint"]
    confidence: Literal["high", "medium", "low"]


# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a strict data extraction engine for a building-materials store.
Extract details from the customer message into this exact JSON structure:
{
  "items": [{"name": string, "quantity": number | null, "unit": string | null}],
  "intent": "order" | "inquiry" | "complaint",
  "confidence": "high" | "medium" | "low"
}
Rules:
- intent "order" = customer wants to buy something
- intent "inquiry" = customer asks about availability/price/stock
- intent "complaint" = customer reports a problem
- Output ONLY valid JSON. No conversational filler. No markdown.

Few-shot examples:
User: I'd like 3 bags of cement and 2 tins of paint please
Assistant: {"items":[{"name":"cement","quantity":3,"unit":"bag"},{"name":"paint","quantity":2,"unit":"tin"}],"intent":"order","confidence":"high"}

User: Do you have white tiles available in stock?
Assistant: {"items":[{"name":"white tiles","quantity":null,"unit":null}],"intent":"inquiry","confidence":"high"}

User: The bricks I received last week were all broken!
Assistant: {"items":[{"name":"bricks","quantity":null,"unit":null}],"intent":"complaint","confidence":"high"}
"""


# ─── Extractor Class ──────────────────────────────────────────────────────────

class OrderExtractor:
    """
    Extracts order information from a WhatsApp message.
    Uses Ollama when MOCK_MODE=false, otherwise uses a deterministic mock.
    """

    def __init__(self) -> None:
        self.mock_mode = os.getenv("MOCK_MODE", "true").lower() == "true"
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "gemma3:4b")

    def extract(self, message: str) -> MessageExtraction:
        if self.mock_mode:
            return self._mock_extract(message)
        return self._ollama_extract(message)

    # ── Mock extraction (deterministic, no external deps) ──────────────────────

    def _mock_extract(self, message: str) -> MessageExtraction:
        """
        Rule-based mock extractor. Sufficient for CI test runs.
        Detects intent via keywords, then parses simple quantity patterns.
        """
        msg_lower = message.lower()

        # Intent detection
        complaint_keywords = ["broken", "damaged", "wrong", "complaint", "issue", "problem", "missing"]
        inquiry_keywords = ["available", "stock", "price", "do you have", "how much", "is there", "check"]

        if any(kw in msg_lower for kw in complaint_keywords):
            intent: Literal["order", "inquiry", "complaint"] = "complaint"
        elif any(kw in msg_lower for kw in inquiry_keywords):
            intent = "inquiry"
        else:
            intent = "order"

        # Simple item/quantity extraction via regex
        # Matches patterns like: "3 bags of cement", "2 tins of paint", "10 pieces of tile"
        pattern = re.compile(
            r"(\d+(?:\.\d+)?)\s+"
            r"(bags?|tins?|pieces?|pcs?|units?|boxes?|rolls?|sheets?|kg|liters?|litres?|meters?|m)?\s*"
            r"(?:of\s+)?"
            r"([a-zA-Z][a-zA-Z\s]{1,30}?)(?=\s*(?:and|,|$|\.))",
            re.IGNORECASE,
        )
        items: list[OrderItem] = []
        for m in pattern.finditer(message):
            qty_str, unit, name = m.group(1), m.group(2), m.group(3).strip()
            items.append(OrderItem(
                name=name,
                quantity=float(qty_str),
                unit=unit.rstrip("s").lower() if unit else None,
            ))

        # If no structured items found, extract nouns as best-effort
        if not items:
            # Grab any capitalised or meaningful nouns after "have" / "about" / generic
            noun_pattern = re.compile(r"\b([a-zA-Z]{3,}(?:\s+[a-zA-Z]{3,})?)\b")
            stopwords = {
                "the", "and", "for", "you", "are", "was", "have", "with",
                "that", "this", "from", "all", "can", "been", "has", "had",
                "please", "hello", "would", "like", "could", "about", "your",
                "last", "week", "they", "were",
            }
            for m in noun_pattern.finditer(message):
                word = m.group(1).lower()
                if word not in stopwords and len(word) > 3:
                    items.append(OrderItem(name=word, quantity=None, unit=None))
                    break  # take first meaningful noun only

        confidence: Literal["high", "medium", "low"] = "high" if items else "low"
        return MessageExtraction(items=items, intent=intent, confidence=confidence)

    # ── Ollama extraction ──────────────────────────────────────────────────────

    def _ollama_extract(self, message: str) -> MessageExtraction:
        payload = json.dumps({
            "model": self.model,
            "prompt": f"{SYSTEM_PROMPT}\n\nUser: {message}\nAssistant:",
            "stream": False,
            "format": "json",
        }).encode()

        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                raw = json.loads(data["response"])
                return MessageExtraction(**raw)
        except (urllib.error.URLError, json.JSONDecodeError, KeyError):
            # Fallback to mock if Ollama is unreachable or returns bad JSON
            return self._mock_extract(message)

