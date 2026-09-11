"""
Q1 — AI WhatsApp Order Extractor
FastAPI webhook endpoint that receives WhatsApp-style messages,
extracts order intent via LLM (or mock), and returns structured JSON.
"""

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from extractor import OrderExtractor, MessageExtraction

app = FastAPI(title="Injani AI Order Extractor", version="1.0.0")

# Instantiate extractor once (respects MOCK_MODE env var)
extractor = OrderExtractor()


@app.post("/webhook", response_model=MessageExtraction)
async def webhook(request: Request) -> JSONResponse:
    """
    Receives an incoming WhatsApp message payload and returns
    structured extraction: items, intent, confidence.
    """
    body = await request.json()
    message_text: str = body.get("message", "")

    if not message_text:
        return JSONResponse(status_code=422, content={"detail": "Field 'message' is required."})

    result = extractor.extract(message_text)
    return JSONResponse(content=result.model_dump())


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "mock_mode": os.getenv("MOCK_MODE", "false").lower() == "true"}

