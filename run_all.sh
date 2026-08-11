#!/usr/bin/env bash
# Reproduce everything in this repository from a clean checkout.
#   bash run_all.sh
# Writes every artifact under results/ and the full console transcript to
# results/run_log.txt.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results

{
  echo "### PinchCatcher reproduction - full run"
  echo "### $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  python3 --version
  echo

  echo "=== 1/5  inner-loop mechanism smoke test ==============================="
  python3 src/smoke_test.py --json results/smoke_test.json

  echo
  echo "=== 2/5  internal-consistency audit of the paper's printed numbers ====="
  python3 src/audit_reported_stats.py --json results/audit.json

  echo
  echo "=== 3/5  sensitivity of the inner loop to the unstated decisions ======="
  python3 src/sensitivity.py --json results/sensitivity.json

  echo
  echo "=== 4/5  recovering unstated parameters from the reported means ========"
  python3 src/recover_unstated_params.py --json results/recovered_params.json

  echo
  echo "=== 5/5  analysis pipeline on synthetic data of the paper's shape ======"
  python3 src/make_synthetic_log.py --mode null --out results/synthetic_null.csv \
      --questionnaire-out results/synthetic_questionnaire.csv
  python3 src/analyze.py results/synthetic_null.csv \
      --questionnaire results/synthetic_questionnaire.csv \
      --outdir results/analysis_null
  echo
  python3 src/make_synthetic_log.py --mode planted --out results/synthetic_planted.csv
  python3 src/analyze.py results/synthetic_planted.csv --outdir results/analysis_planted

  echo
  echo "### done"
} 2>&1 | tee results/run_log.txt
