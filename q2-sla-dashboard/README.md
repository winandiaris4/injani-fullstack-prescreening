# Q2 — SLA Analytics Dashboard

PoC untuk menjawab **Question 2** dari pre-screening INJANI SYSTEMS.

## Overview

Dashboard analitik SLA untuk approval workflow system berbasis Next.js 14 App Router.
Menggunakan React Server Components untuk data fetching langsung di server, dan Prisma + SQLite agar bisa dijalankan tanpa setup database eksternal.

## Cara Menjalankan

### 1. Install dependencies
```bash
npm install
```

### 2. Setup database (SQLite)
```bash
DATABASE_URL="file:./dev.db" npx prisma db push
```

### 3. Seed dummy data
```bash
DATABASE_URL="file:./dev.db" npm run db:seed
```

### 4. Jalankan server
```bash
npm run dev
# Buka: http://localhost:3000
```

## Arsitektur Next.js

```
app/
├── page.tsx               ← RSC Dashboard (fetch + render di server)
└── api/
    └── sla/
        └── route.ts       ← API Route: aggregated SLA analytics

prisma/
└── schema.prisma          ← SQLite schema (bisa diganti PostgreSQL)

lib/
└── seed.ts               ← Dummy data generator (80 workflows)
```

## Schema Database

```sql
departments      → id, name
users            → id, name, department_id
step_types       → id, name, sla_target_minutes   ← SLA threshold per step
workflows        → id, title, department_id, status, created_at
workflow_steps   → id, workflow_id, step_type_id, assignee_id,
                   assigned_at, completed_at
```

`duration_minutes` dihitung saat query: `(completed_at - assigned_at) / 60`

## Dashboard Components

| Komponen | Insight Bisnis |
|---|---|
| **Summary Cards** | Total workflow, total steps, breach rate % |
| **Bar Chart** | Avg Duration vs SLA Target per Step Type → identifikasi bottleneck |
| **Breached Workflows Table** | Top workflow yang terlambat → actionable untuk eskalasi |

## Switch ke PostgreSQL

Ubah `prisma/schema.prisma`:
```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
```

Dan set `DATABASE_URL` ke PostgreSQL connection string.

## Tech Stack

- **Next.js 14** — App Router + React Server Components
- **Prisma** — ORM dengan SQLite (PoC) / PostgreSQL (produksi)
- **TypeScript** — Type safety end-to-end

