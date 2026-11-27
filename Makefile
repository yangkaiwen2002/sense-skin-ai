.PHONY: setup dev check evaluate smoke
setup:
	python3 -m venv backend/.venv
	backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
	cd frontend && npm ci

dev:
	./scripts/dev.sh

check:
	OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 backend/.venv/bin/python -m pytest backend/tests -q
	cd frontend && npm run typecheck && npm test && npm run build

evaluate:
	cd backend && .venv/bin/python -m app.rag.evaluation --output evaluation/latest.json --baseline evaluation/results.json

smoke:
	python3 scripts/smoke-agent.py --require-generated
