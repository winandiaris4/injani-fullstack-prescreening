-- Q4 — PostgreSQL Query Performance: Create Indexes
-- Strategi indexing untuk query: WHERE user_id = ? AND status = ? AND created_at BETWEEN ? AND ?

-- ─── 1. Composite Index (Primary Optimization) ────────────────────────────────
-- Urutan kolom: Equality columns first (user_id, status), Range column last (created_at)
-- Prinsip: B-Tree index efisien jika kolom filter presisi diletakkan lebih awal.
CREATE INDEX CONCURRENTLY idx_transactions_user_status_created
    ON transactions (user_id, status, created_at DESC);

-- ─── 2. Partial Index (Jika sering query status PENDING saja) ────────────────
-- Mengindeks hanya subset baris yang memenuhi kondisi WHERE status = 'PENDING'
-- Keuntungan: Index jauh lebih kecil di RAM → lebih cepat untuk query spesifik ini
CREATE INDEX CONCURRENTLY idx_transactions_pending_user_created
    ON transactions (user_id, created_at DESC)
    WHERE status = 'PENDING';

-- ─── 3. Covering Index (Index-Only Scan) ─────────────────────────────────────
-- Menyertakan kolom SELECT yang sering dipakai langsung di index (INCLUDE clause)
-- Keuntungan: PostgreSQL tidak perlu mengakses heap table sama sekali (Index-Only Scan)
CREATE INDEX CONCURRENTLY idx_transactions_covering
    ON transactions (user_id, status, created_at DESC)
    INCLUDE (amount);  -- kolom sering di-SELECT, tidak di-filter

-- ─── Update statistik setelah index dibuat ───────────────────────────────────
ANALYZE transactions;

-- ─── Verifikasi index yang aktif ─────────────────────────────────────────────
SELECT
    indexname,
    indexdef,
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size
FROM pg_indexes
WHERE tablename = 'transactions'
ORDER BY pg_relation_size(indexname::regclass) DESC;

