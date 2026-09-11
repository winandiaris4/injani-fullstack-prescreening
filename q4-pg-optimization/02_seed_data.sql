-- Q4 — PostgreSQL Query Performance: Seed Data
-- Generate 500.000 baris dummy data yang realistis.
-- Distribusi status, user_id, dan tanggal dibuat acak namun terkontrol.
-- Catatan: Di produksi gunakan 10 juta+ baris untuk representasi akurat.

-- ─── Generate 500k rows dengan generate_series ───────────────────────────────
INSERT INTO transactions (user_id, status, amount, description, created_at, updated_at)
SELECT
    -- user_id: distribusi 1–2000 (simulasi 2000 user aktif)
    (random() * 1999 + 1)::INT AS user_id,

    -- status: COMPLETED 60%, PENDING 25%, FAILED 10%, REFUNDED 5%
    CASE
        WHEN random() < 0.60 THEN 'COMPLETED'
        WHEN random() < 0.85 THEN 'PENDING'
        WHEN random() < 0.95 THEN 'FAILED'
        ELSE 'REFUNDED'
    END AS status,

    -- amount: distribusi log-normal (banyak transaksi kecil, sedikit besar)
    ROUND((exp(random() * 4 + 3))::NUMERIC, 2) AS amount,

    -- description: variasi teks pendek
    'Transaction #' || i || ' - ' ||
    (ARRAY['Order payment', 'Top up', 'Refund', 'Service fee', 'Withdrawal'])[floor(random()*5)+1]
        AS description,

    -- created_at: spread dalam 2 tahun terakhir
    NOW() - (random() * INTERVAL '730 days') AS created_at,

    NOW() - (random() * INTERVAL '730 days') AS updated_at

FROM generate_series(1, 500000) AS s(i);

-- ─── Update statistics ────────────────────────────────────────────────────────
ANALYZE transactions;

-- ─── Verifikasi ───────────────────────────────────────────────────────────────
SELECT
    COUNT(*)         AS total_rows,
    MIN(created_at)  AS oldest_transaction,
    MAX(created_at)  AS newest_transaction,
    COUNT(DISTINCT user_id) AS unique_users
FROM transactions;

SELECT status, COUNT(*) AS count, ROUND(COUNT(*)*100.0/500000, 1) AS pct
FROM transactions
GROUP BY status
ORDER BY count DESC;

