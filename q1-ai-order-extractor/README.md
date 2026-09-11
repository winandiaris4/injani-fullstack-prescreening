# Q1 — AI WhatsApp Order Extractor

PoC untuk menjawab **Question 1** dari pre-screening INJANI SYSTEMS.

## Overview

Sistem ekstraksi intent order dari pesan WhatsApp menggunakan LLM lokal (Ollama/Gemma) atau rule-based mock untuk testing.

## Arsitektur

```
[ WhatsApp Webhook ]
        │ (HTTP POST)
        ▼
[ FastAPI /webhook ]
        │
        ▼
[ OrderExtractor ]
   ├── MOCK_MODE=true  → Regex rule-based (no GPU needed)
   └── MOCK_MODE=false → Ollama API (Gemma 3 4B)
        │
        ▼
[ Pydantic MessageExtraction ]
   ├── VALID   → Return structured JSON
   └── INVALID → Fallback mock + flag for review
```

## Cara Menjalankan

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run tests (MOCK_MODE)
```bash
MOCK_MODE=true pytest test_evaluation.py -v
```

### 3. Run FastAPI server
```bash
# Mode mock (tanpa Ollama)
MOCK_MODE=true uvicorn app:app --reload

# Mode Ollama (butuh Ollama running di localhost:11434)
MOCK_MODE=false OLLAMA_MODEL=gemma3:4b uvicorn app:app --reload
```

### 4. Test webhook
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "I'\''d like 3 bags of cement and 2 tins of paint please"}'
```

**Response:**
```json
{
  "items": [
    {"name": "cement", "quantity": 3.0, "unit": "bag"},
    {"name": "paint", "quantity": 2.0, "unit": "tin"}
  ],
  "intent": "order",
  "confidence": "high"
}
```

## Output Schema (Pydantic)

| Field | Type | Description |
|---|---|---|
| `items[].name` | `str` | Nama produk/item |
| `items[].quantity` | `float \| null` | Jumlah (null jika tidak disebutkan) |
| `items[].unit` | `str \| null` | Satuan (bag, tin, piece, kg, dll) |
| `intent` | `order \| inquiry \| complaint` | Klasifikasi intent pesan |
| `confidence` | `high \| medium \| low` | Tingkat keyakinan ekstraksi |

## Evaluasi (Golden Dataset)

Dataset berlabel manual: **22 pesan** (mix Bahasa Inggris & Indonesia).

| Metric | Target | Keterangan |
|---|---|---|
| Intent Accuracy | ≥ 70% | Dihitung dari golden_dataset.json |
| Schema Validity | ≥ 99% | Output selalu Pydantic-valid |
| Fallback Rate | < 5% | Mock fallback jika Ollama unreachable |

## Environment Variables

| Variable | Default | Keterangan |
|---|---|---|
| `MOCK_MODE` | `true` | `true` = rule-based, `false` = Ollama |
| `OLLAMA_URL` | `http://localhost:11434` | Alamat Ollama server |
| `OLLAMA_MODEL` | `gemma3:4b` | Model yang digunakan |

