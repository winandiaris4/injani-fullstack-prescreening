# Injani Systems — Fullstack Developer Pre-Screening PoC

![CI](https://github.com/winandiaris4/injani-fullstack-prescreening/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-green)

> Proof of Concept (PoC) fungsional untuk setiap jawaban teknis pada pre-screening **Fullstack Developer** INJANI SYSTEMS.
> Setiap modul berdiri sendiri, bisa dijalankan secara lokal, dan dilengkapi dengan automated tests.

---

## 👤 Tentang

**Aris Winandi** — Back-End Developer (Python · Django · FastAPI · GCP)
- 🌐 [ariswinandi.com](https://ariswinandi.com) | 💼 [LinkedIn](https://www.linkedin.com/in/ariswinandi/) | 🐙 [GitHub](https://github.com/winandiaris4)

---

## 🗂️ Daftar Modul PoC

| Modul | Soal | Teknologi | Test |
|---|---|---|---|
| [q1-ai-order-extractor/](./q1-ai-order-extractor/) | Q1 — AI WhatsApp Order Processing | Python · FastAPI · Pydantic | `pytest` ✅ |
| [q2-sla-dashboard/](./q2-sla-dashboard/) | Q2 — SLA Analytics Dashboard | Next.js 14 · Prisma · SQLite | `npm build` ✅ |
| [q3-cloud-tasks-worker/](./q3-cloud-tasks-worker/) | Q3 — Cloud Tasks Testing & Monitoring | Python · FastAPI · Pytest | `pytest` ✅ |
| [q4-pg-optimization/](./q4-pg-optimization/) | Q4 — PostgreSQL Query Performance | SQL · EXPLAIN ANALYZE | Manual SQL |
| [q5-nextjs-api-patterns/](./q5-nextjs-api-patterns/) | Q5 — Next.js Auth, Rate Limit & Errors | Next.js 14 · jose · Jest | `jest` ✅ |
| [q6-async-worker-patterns/](./q6-async-worker-patterns/) | Q6 — Async Background Jobs | Python · FastAPI · ARQ · fakeredis | `pytest` ✅ |
| [.github/workflows/ci.yml](./.github/workflows/ci.yml) | Q7 — CI/CD Pipeline | GitHub Actions | Badge above 🟢 |

---

## 🛠️ Tech Stack

```
Backend    : Python 3.12 · FastAPI · Pydantic · ARQ · fakeredis
Frontend   : Next.js 14 (App Router) · TypeScript · React Server Components
Database   : PostgreSQL (production) · SQLite via Prisma (PoC)
AI/ML      : Ollama/Gemma 3 (self-hosted) · MOCK_MODE for testing
Cloud      : GCP Cloud Tasks · Cloud Run · Cloud SQL · Secret Manager
CI/CD      : GitHub Actions (Lint → Test → Build)
```

---

## ⚡ Quick Start per Modul

### Q1 — AI Order Extractor
```bash
cd q1-ai-order-extractor
pip install -r requirements.txt
MOCK_MODE=true pytest -v          # Run tests (no Ollama needed)
MOCK_MODE=true uvicorn app:app --reload  # Run server
```

### Q2 — SLA Dashboard
```bash
cd q2-sla-dashboard
npm ci
npx prisma db push                # Create SQLite schema
npm run db:seed                   # Fill with dummy data
npm run dev                       # Open http://localhost:3000
```

### Q3 — Cloud Tasks Worker
```bash
cd q3-cloud-tasks-worker
pip install -r requirements.txt
pytest -v                         # Run all tests
```

### Q4 — PostgreSQL Optimization
```bash
cd q4-pg-optimization
psql -U postgres -d mydb
# \i 01_create_table.sql
# \i 02_seed_data.sql
# \i 03_before_index.sql    # See slow query (~300ms)
# \i 04_create_indexes.sql
# \i 05_after_index.sql     # See fast query (~0.4ms)
```

### Q5 — Next.js API Patterns
```bash
cd q5-nextjs-api-patterns
npm ci
npm test                          # Run Jest unit tests
```

### Q6 — Async Worker Patterns
```bash
cd q6-async-worker-patterns
pip install -r requirements.txt
pytest -v                         # Run all tests (fakeredis, no real Redis)
```

---

## 📊 Q4 Benchmark Highlights

| Metric | Before Index | After Index |
|---|---|---|
| Scan Type | `Seq Scan` | `Index Scan` |
| Execution Time | ~312 ms | ~0.4 ms |
| Rows Scanned | 500,000 | 82 |
| Buffer Pages | 12,543 | 6 |

> **800x speedup** with a composite index: `(user_id, status, created_at DESC)`

---

## 🏗️ Arsitektur Q7 — CI/CD Pipeline

```
Push to main
     │
     ├── [backend-ci]     → ruff check → pytest Q1 + Q3 + Q6
     ├── [frontend-q2]    → npm ci → prisma generate → lint → build
     └── [frontend-q5]    → npm ci → lint → jest
```

Semua jobs berjalan paralel. Badge CI di atas mencerminkan status build terkini.

---

## 🔗 Referensi

- 📄 [Panduan Lengkap Jawaban Pre-Test](../project-analytic/job-opportunity/INJANI_SYSTEMS/panduan-lengkap-pretest.md)
- 📋 [Rencana PoC](../project-analytic/job-opportunity/INJANI_SYSTEMS/poc-injani-plan.md)
