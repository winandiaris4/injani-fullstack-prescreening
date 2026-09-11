-- Q4 — PostgreSQL Query Performance: Create Table
-- DDL untuk tabel transactions (10 juta baris di produksi)
-- Jalankan file ini terlebih dahulu sebelum file lain.

-- ─── Cleanup (jika re-run) ────────────────────────────────────────────────────
DROP TABLE IF EXISTS transactions;

-- ─── Main Table ───────────────────────────────────────────────────────────────
CREATE TABLE transactions (
    id          BIGSERIAL    PRIMARY KEY,
    user_id     INT          NOT NULL,
    status      VARCHAR(20)  NOT NULL,           -- 'PENDING', 'COMPLETED', 'FAILED', 'REFUNDED'
    amount      NUMERIC(12,2) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ─── Komentar ─────────────────────────────────────────────────────────────────
COMMENT ON TABLE transactions IS
    'Tabel transaksi utama. Di produksi berisi 10 juta+ baris.';
COMMENT ON COLUMN transactions.status IS
    'Status transaksi: PENDING | COMPLETED | FAILED | REFUNDED';
COMMENT ON COLUMN transactions.user_id IS
    'Foreign key ke tabel users (disederhanakan untuk PoC)';

