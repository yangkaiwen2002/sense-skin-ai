#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
if [[ ! -x backend/.venv/bin/python || ! -d frontend/node_modules ]]; then
  echo "Run make setup first (Python 3.12+, Node 22.12+)."; exit 1
fi
pids=()
cleanup() {
  for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
  for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
MODEL_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
if [[ -x .runtime/ollama/ollama && -z "${OLLAMA_URL:-}" ]]; then
  MODEL_URL=http://127.0.0.1:11435
  if ! curl -fsS "$MODEL_URL/api/tags" >/dev/null 2>&1; then
    OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11435 OLLAMA_MODELS="$ROOT/.runtime/models" .runtime/ollama/ollama serve > .runtime/ollama-dev.log 2>&1 &
    pids+=("$!")
  fi
fi
(cd backend && exec env DATA_MODE=mock DATABASE_URL=sqlite:///./senseskin-demo.db AI_PROVIDER=ollama OLLAMA_URL="$MODEL_URL" .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --timeout-graceful-shutdown 5) &
pids+=("$!")
(cd frontend && exec node node_modules/vite/bin/vite.js --host 127.0.0.1 --strictPort) &
pids+=("$!")
echo "SenseSkin: http://localhost:5173 | Mock business data + local Ollama: $MODEL_URL"
wait
