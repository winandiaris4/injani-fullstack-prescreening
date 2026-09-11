-- Q4 — PostgreSQL Query Performance: Before Index (Slow Query)
-- Jalankan setelah 02_seed_data.sql untuk melihat performa TANPA index.
-- Output EXPLAIN ANALYZE dicantumkan sebagai komentar referensi di bawah.

-- ─── Query yang akan dioptimasi ───────────────────────────────────────────────
-- Filter: user_id + status + date range
-- Tanpa index → PostgreSQL terpaksa melakukan Sequential Scan penuh

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id, user_id, status, amount, created_at
FROM transactions
WHERE user_id = 1050
  AND status = 'COMPLETED'
  AND created_at >= '2026-01-01'
  AND created_at <  '2026-07-01';

/*
═══════════════════════════════════════════════════════════════════════════════
 EXAMPLE OUTPUT (tanpa index, 500k baris):
═══════════════════════════════════════════════════════════════════════════════

 Seq Scan on transactions  (cost=0.00..17543.00 rows=35 width=52)
                           (actual time=0.062..312.847 rows=82 loops=1)
   Filter: ((user_id = 1050) AND ((status)::text = 'COMPLETED') AND
            (created_at >= '2026-01-01') AND (created_at < '2026-07-01'))
   Rows Removed by Filter: 499918
   Buffers: shared hit=7043 read=5500
 Planning Time: 0.123 ms
 Execution Time: 312.891 ms     ← ⚠️ 312ms untuk 500k baris!
                                   Bayangkan 10 juta baris = 4+ detik

 Diagnosis:
   - "Seq Scan" → membaca SEMUA 500k baris satu per satu
   - "Rows Removed by Filter: 499918" → hanya 82 baris relevan dari 500k
   - "Buffers: shared read=5500" → banyak I/O ke disk (cache miss)
   - Ini adalah N-full table scan yang sangat tidak efisien
═══════════════════════════════════════════════════════════════════════════════
*/

