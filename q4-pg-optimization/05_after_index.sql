-- Q4 — PostgreSQL Query Performance: After Index (Optimized Query)
-- Jalankan setelah 04_create_indexes.sql.
-- Query IDENTIK dengan 03_before_index.sql — hanya index yang berbeda.

-- ─── Query sama, sekarang PostgreSQL akan memilih index ───────────────────────
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id, user_id, status, amount, created_at
FROM transactions
WHERE user_id = 1050
  AND status = 'COMPLETED'
  AND created_at >= '2026-01-01'
  AND created_at <  '2026-07-01';

/*
═══════════════════════════════════════════════════════════════════════════════
 EXAMPLE OUTPUT (setelah composite index):
═══════════════════════════════════════════════════════════════════════════════

 Index Scan using idx_transactions_user_status_created on transactions
   (cost=0.42..12.71 rows=82 width=52)
   (actual time=0.045..0.312 rows=82 loops=1)
   Index Cond: ((user_id = 1050) AND (status = 'COMPLETED')
                AND (created_at >= '2026-01-01') AND (created_at < '2026-07-01'))
   Buffers: shared hit=6    ← ✅ hanya 6 buffer pages (vs 12543 sebelumnya!)
 Planning Time: 0.231 ms
 Execution Time: 0.387 ms   ← ✅ 0.4ms! (vs 312ms sebelumnya)

 Analisis:
   - "Index Scan" → hanya membaca baris relevan saja
   - "Buffers: shared hit=6" → hampir semuanya dari RAM cache (bukan disk)
   - Tidak ada "Rows Removed by Filter" → index sudah presisi
═══════════════════════════════════════════════════════════════════════════════
*/

-- ─── Test Covering Index (Index-Only Scan) ────────────────────────────────────
-- Query yang hanya mengambil kolom yang ada di INCLUDE clause:
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT user_id, status, created_at, amount
FROM transactions
WHERE user_id = 1050
  AND status = 'COMPLETED'
  AND created_at >= '2026-01-01'
  AND created_at <  '2026-07-01';

/*
 Index Only Scan using idx_transactions_covering on transactions
   (cost=0.42..8.14 rows=82 width=44)
   (actual time=0.031..0.124 rows=82 loops=1)
   Heap Fetches: 0    ← ✅ Tidak ada akses ke heap table sama sekali!
   Buffers: shared hit=3
 Execution Time: 0.151 ms   ← ✅ Bahkan lebih cepat dari Index Scan!
*/

