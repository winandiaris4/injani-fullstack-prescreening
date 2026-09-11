-- Q4 — PostgreSQL Query Performance: Table Partitioning
-- Implementasi RANGE partitioning berdasarkan created_at (per tahun/bulan).
-- Keuntungan: Partition Pruning → PostgreSQL hanya scan partisi yang relevan.

-- ─── Buat tabel partisi baru ──────────────────────────────────────────────────
DROP TABLE IF EXISTS transactions_partitioned CASCADE;

CREATE TABLE transactions_partitioned (
    id          BIGSERIAL,
    user_id     INT          NOT NULL,
    status      VARCHAR(20)  NOT NULL,
    amount      NUMERIC(12,2) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)   -- PK harus include partition key
) PARTITION BY RANGE (created_at);

-- ─── Buat partisi per tahun ───────────────────────────────────────────────────
CREATE TABLE transactions_2025
    PARTITION OF transactions_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE transactions_2026
    PARTITION OF transactions_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- Future partition
CREATE TABLE transactions_2027
    PARTITION OF transactions_partitioned
    FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');

-- ─── Default partition (untuk data di luar range yang didefinisikan) ──────────
CREATE TABLE transactions_default
    PARTITION OF transactions_partitioned
    DEFAULT;

-- ─── Index pada setiap partisi (otomatis di-inherit dari parent) ──────────────
CREATE INDEX ON transactions_partitioned (user_id, status, created_at DESC);

-- ─── Demonstrasi Partition Pruning ───────────────────────────────────────────
-- Query dengan filter created_at → PostgreSQL hanya scan partisi 2026, skip yang lain

EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*)
FROM transactions_partitioned
WHERE user_id = 1050
  AND created_at >= '2026-01-01'
  AND created_at <  '2026-07-01';

/*
 Expected output dengan Partition Pruning:
 ─────────────────────────────────────────
 Aggregate  (cost=24.50..24.51 rows=1 width=8)
   ->  Index Scan using transactions_2026_user_id_status_created_at_idx
         on transactions_2026 transactions_partitioned
       Index Cond: ...
 Subplans Removed: 3   ← ✅ Partisi 2025, 2027, default di-skip otomatis!
*/

-- ─── Contoh Auto-Maintenance: Tambah partisi baru tanpa downtime ──────────────
-- Jalankan ini di awal setiap tahun (atau via scheduled job):
/*
CREATE TABLE transactions_2028
    PARTITION OF transactions_partitioned
    FOR VALUES FROM ('2028-01-01') TO ('2029-01-01');
*/

-- ─── Contoh Drop partisi lama (archiving) ─────────────────────────────────────
-- Untuk mengarsip data lama dengan zero-cost (jauh lebih cepat dari DELETE):
/*
ALTER TABLE transactions_partitioned DETACH PARTITION transactions_2024;
-- Kemudian dump ke cold storage:
-- pg_dump -t transactions_2024 mydb > transactions_2024_archive.sql
-- DROP TABLE transactions_2024;
*/

