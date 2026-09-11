.PHONY: help up down test test-q1 test-q2 test-q3 test-q4 test-q5 test-q6 q1 q2 q3 q5 q6 psql logs

help:
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║        🚀 INJANI SYSTEMS PRE-SCREENING POC COMMANDS              ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  ▶ Menjalankan Service (Docker):"
	@echo "    make up          - Menjalankan SEMUA modul & database di background"
	@echo "    make down        - Menghentikan semua container"
	@echo "    make q1          - Jalankan Q1 AI Extractor (http://localhost:8000)"
	@echo "    make q2          - Jalankan Q2 SLA Dashboard (http://localhost:3000)"
	@echo "    make q3          - Jalankan Q3 Cloud Tasks Worker (http://localhost:8003)"
	@echo "    make q5          - Jalankan Q5 API Patterns (http://localhost:3001)"
	@echo "    make q6          - Jalankan Q6 Async Worker & SSE (http://localhost:8002)"
	@echo ""
	@echo "  ▶ Menjalankan Automated Tests & Build Verification (Docker):"
	@echo "    make test        - Jalankan SEMUA test & build (Q1 s/d Q6)"
	@echo "    make test-q1     - Jalankan evaluasi akurasi dataset Q1"
	@echo "    make test-q2     - Validasi Lint, Typecheck & Production Build Q2"
	@echo "    make test-q3     - Jalankan test Cloud Tasks Q3"
	@echo "    make test-q4     - Verifikasi database PostgreSQL Q4"
	@echo "    make test-q5     - Jalankan Jest unit tests Q5"
	@echo "    make test-q6     - Jalankan test Idempotency & SSE Q6"
	@echo ""
	@echo "  ▶ Database & Debugging:"
	@echo "    make psql        - Masuk ke psql PostgreSQL 16 (Q4 Benchmark)"
	@echo "    make logs        - Tampilkan log semua service"
	@echo ""

up:
	docker compose up --build -d

down:
	docker compose down

q1:
	docker compose up --build q1-extractor

q2:
	docker compose up --build q2-dashboard

q3:
	docker compose up --build q3-worker

q5:
	docker compose up --build q5-api

q6:
	docker compose up --build q6-async

test: test-q1 test-q2 test-q3 test-q5 test-q6
	@echo "\n🎉 ALL TESTS & BUILDS PASSED SUCCESSFULLY! ✅\n"

test-q1:
	docker compose run --rm q1-extractor pytest test_evaluation.py -v -s

test-q2:
	docker compose run --rm q2-dashboard sh -c "npx prisma generate && npm run lint && npx tsc --noEmit && npm run build"

test-q3:
	docker compose run --rm q3-worker pytest test_worker.py -v -s

test-q4:
	docker compose up -d postgres
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 2
	docker exec injani-postgres psql -U postgres -d injani_poc -c "SELECT count(*) FROM transactions;"

test-q5:
	docker compose run --rm q5-api npm test

test-q6:
	docker compose run --rm q6-async pytest test_idempotency.py -v -s

psql:
	docker exec -it injani-postgres psql -U postgres -d injani_poc

logs:
	docker compose logs -f

