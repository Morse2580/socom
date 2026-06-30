#!/usr/bin/env bash
# Regenerate the SOCOM Phase-0 pilot baseline.
#
# Runs every bench task (bench/tasks/B-*.xml) through the REAL Phase-2 measurement
# spine — `socom contract verify --record` -> the run ledger -> `socom cycle` — and
# freezes a committed snapshot under bench/baseline/. This is the "before" picture
# the Phase-3 A/B (SOCOM-on vs SOCOM-off) diffs against. Replayable evidence:
#
#   bash bench/run_baseline.sh
#
# The single number that matters: tasks completing GREEN with ZERO human
# intervention (every check is auto, so the whole set is mechanically scored).
set -u

cd "$(dirname "$0")/.." || exit 2
[ -x bin/socom ] && [ -d bench/tasks ] || {
  echo "run from the socom repo root (need ./bin/socom and bench/tasks/)" >&2
  exit 2
}

LEDGER=.socom/ledger/runs.jsonl   # .socom is generated, gitignored scratch here
BASE=bench/baseline
mkdir -p "$BASE" "$(dirname "$LEDGER")"

# Start the bench ledger clean so the snapshot is exactly this run's task set.
: > "$LEDGER"

kept=0 broken=0 total=0
{
  echo "# SOCOM Phase-0 baseline — captured by bench/run_baseline.sh"
  echo "# task<TAB>verdict<TAB>exit"
} > "$BASE/summary.tsv"

for t in bench/tasks/B-*.xml; do
  total=$((total + 1))
  if ./bin/socom contract verify --record "$t" > "/tmp/socom-bench.$$" 2>&1; then
    verdict=kept; kept=$((kept + 1)); rc=0
  else
    verdict=broken; broken=$((broken + 1)); rc=$?
  fi
  printf '%s\t%s\t%s\n' "$(basename "$t" .xml)" "$verdict" "$rc" >> "$BASE/summary.tsv"
  echo "  [$verdict] $(basename "$t")"
done
rm -f "/tmp/socom-bench.$$"

# Freeze the captured rows + the rolled cycle as the diffable evidence.
cp "$LEDGER" "$BASE/runs.jsonl"
./bin/socom cycle > "$BASE/cycle.txt" 2>&1 || true

echo
echo "baseline: $kept kept / $broken broken across $total tasks  (zero-human-intervention green = $kept/$total)"
echo "frozen -> $BASE/{summary.tsv,runs.jsonl,cycle.txt}"
