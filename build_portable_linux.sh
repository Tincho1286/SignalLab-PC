#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$project_root"
if [[ ! -x .venv/bin/python ]]; then
  printf '%s\n' 'Primero prepará .venv con Python 3.12 e instalá requirements-lock.txt.' >&2
  exit 1
fi
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
exec .venv/bin/python -B tools/build_linux_portable.py
