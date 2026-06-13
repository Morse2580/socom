<!-- hand-authored 2026-06-13 — first SOCOM session prompt; next closeout's `socom prompt` regenerates it -->
# Next session — SOCOM: extract **evals** (the measurement backbone) from Akili

You are maturing the **SOCOM** substrate. Standing focus (operator, 2026-06-13): port proven
capabilities from the Akili platform (`~/Documents/projs/Akili`, the mature original SOCOM was
extracted from) into SOCOM — one per session, distilled and matured, **the pattern not the
code**. The ranked plan is `EXTRACTION-BACKLOG.md` (committed). **First target: evals.**

Begin by:
1. `socom gate session-start` (drift + orphan reaper).
2. Read `EXTRACTION-BACKLOG.md` (the §"#1 — Evals" section is your spec), then the Akili
   source it points at — read 1–2 `cycle-*.json` fully + skim the `eval_*.py` suite.
3. `socom claim cli` (the deliverable is a `socom eval` command; it also touches `canon`).
4. Plan mode; ratify the contract below before any code.

## The goal — give `verify-never-claim` a scored, replayable spine
Akili's pattern is **ledger → cycle → query**: every agent run appends to a ledger; periodic
cycle rollups compute pass@1 / pass@k / per-role pass-rates / hotspots / efficiency; a query
suite reads them and feeds lessons. SOCOM already has the units to measure — **seats**
executing **promises** against **contracts**, gated at known **bands**. Make their outcomes
measured.

Build, minimal and agent-agnostic:
1. **Run ledger** — a new `schemas/ledger.xml` (+ append format): one row per promise
   execution — seat, promise/task id, contract id, gate band, exit code, duration, attempt,
   verdict. Append-only, in-repo (§git-is-source-of-truth).
2. **`socom eval`** — rolls the ledger into a cycle artifact: pass@1, pass@k **by seat**,
   hotspots (promises that keep failing assessment), contract-coverage. Distil Akili's cycle
   JSON to SOCOM vocabulary (seats not roles, promises not tasks). Read-only, cache-free.
3. **Gate tie-in** — wire the cycle into `canon/gates.xml` so a gate can flag/fail on a
   pass-rate threshold, and repeated failures surface as lesson candidates (backlog #2).

## Validation contract (assessor: an independent reviewer seat)
A check is done only when its command + output is pasted.
1. `schemas/ledger.xml` parses (well-formed) and `tests/` covers it.
2. `socom eval` on a **seeded ledger** emits a cycle artifact with pass@1 + pass@k per seat —
   numbers match the seed by hand-count.
3. A gate (`socom gate <id>`) flags/fails when the seeded pass-rate is below threshold, passes
   above it — both directions shown.
4. `socom doctor` clean; `socom compile` regenerates without drift.

## Source pointers
- `~/Documents/projs/Akili/evals/cycle-*.json` — the rollup shape (read fully)
- `~/Documents/projs/Akili/scripts/akili-graph/commands/eval_{health,reliability,trends,lessons}.py`
- `~/Documents/projs/Akili/LESSON-SYSTEM-ENGINEERING.md` — the eval→lesson bridge (also backlog #2)
- SOCOM targets: `schemas/` (new), `canon/gates.xml`, `bin/socom`, `socom.yaml`, `tests/`.

## Method + scope discipline
Distil the *essential* pattern, not Akili's implementation — SOCOM stays lean. ONE increment:
ledger + `socom eval` + one gate tie-in. Defer the full query suite (health/trends/reliability
as separate flags) and the control-plane policy-evals. Contract-first; keep gates green;
capture the next extraction (lessons) as the closeout's next-session prompt.
