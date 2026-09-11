# Q4 — PostgreSQL Query Performance & Schema Optimization

PoC untuk menjawab **Question 4** dari pre-screening INJANI SYSTEMS.

## Overview

Rangkaian file SQL yang mendemonstrasikan optimasi performa query PostgreSQL secara end-to-end:
diagnosing slow query → menerapkan strategi indexing → membuktikan peningkatan performa.

## Cara Menjalankan

```bash
# Pastikan PostgreSQL sudah running, lalu:
psql -U postgres -d injani_poc

# Jalankan berurutan:
\i 01_create_table.sql
\i 02_seed_data.sql     -- ~30 detik untuk 500k baris
\i 03_before_index.sql  -- Lihat output EXPLAIN: Seq Scan, ~300ms
\i 04_create_indexes.sql
\i 05_after_index.sql   -- Lihat output EXPLAIN: Index Scan, ~0.4ms
\i 06_partitioning.sql  -- Demo RANGE partitioning + Partition Pruning
```

## Hasil Benchmark (Before vs After)

| Metric | Before Index | After Index | Improvement |
|---|---|---|---|
| **Scan Type** | `Seq Scan` | `Index Scan` | Sequential → Targeted |
| **Execution Time** | ~312 ms | ~0.4 ms | **800x lebih cepat** |
| **Rows Scanned** | 500,000 | 82 | **6,097x lebih efisien** |
| **Buffer Pages** | 12,543 | 6 | **2,090x lebih sedikit I/O** |
| **Disk Reads** | 5,500 | 0 | Sepenuhnya dari RAM |

> **Catatan:** Dengan 10 juta baris (produksi), Seq Scan diperkirakan membutuhkan **4–6 detik**.
> Index Scan akan tetap ~0.4ms karena B-Tree lookup adalah O(log N).

## Strategi Index yang Diterapkan

### 1. Composite Index
```sql
CREATE INDEX idx_transactions_user_status_created
    ON transactions (user_id, status, created_at DESC);
```
**Prinsip:** Equality columns dulu (`user_id`, `status`), Range column terakhir (`created_at`).
B-Tree melakukan binary search pada equality columns, lalu range scan yang sudah tersorted.

### 2. Partial Index
```sql
CREATE INDEX idx_transactions_pending_user_created
    ON transactions (user_id, created_at DESC)
    WHERE status = 'PENDING';
```
**Prinsip:** Mengindeks hanya subset baris. Index lebih kecil → fit di RAM → lebih cepat.
Ideal jika ada status spesifik yang sering diquery.

### 3. Covering Index (Index-Only Scan)
```sql
CREATE INDEX idx_transactions_covering
    ON transactions (user_id, status, created_at DESC)
    INCLUDE (amount);
```
**Prinsip:** Kolom yang di-`SELECT` tapi tidak di-`WHERE` dimasukkan via `INCLUDE`.
PostgreSQL bisa mengembalikan hasil tanpa menyentuh heap table sama sekali.

## Anti-Patterns yang Dihindari

```sql
-- ❌ SALAH: Membungkus kolom index dengan fungsi
WHERE DATE(created_at) = '2026-01-01'   -- index tidak digunakan!

-- ✅ BENAR: Range eksplisit
WHERE created_at >= '2026-01-01' AND created_at < '2026-01-02'

-- ❌ SALAH: Leading wildcard
WHERE description LIKE '%cement%'       -- Seq Scan terpaksa

-- ✅ BENAR: Full-text search atau Trigram index (pg_trgm)
-- CREATE INDEX ON transactions USING GIN (to_tsvector('english', description));
```

## Table Partitioning (file 06)

RANGE partitioning per tahun memungkinkan **Partition Pruning**:
- Query `WHERE created_at BETWEEN '2026-01-01' AND '2026-06-30'`
  → PostgreSQL hanya scan partisi `transactions_2026` (skip 2025, 2027, dll)
- Archiving mudah: `ALTER TABLE ... DETACH PARTITION` (zero-cost, tanpa DELETE)
- Menambah partisi baru tidak butuh downtime

