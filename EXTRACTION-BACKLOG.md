# SOCOM extraction backlog — mature the substrate by porting proven Akili capabilities

**Standing focus for upcoming sessions** (operator, 2026-06-13): SOCOM was extracted from the
Akili platform (`~/Documents/projs/Akili`). Akili is the mature 5708-file original; SOCOM is
the lean governance core (6 canon XMLs + 4 schemas + the `socom` CLI). Several Akili
subsystems are proven-in-anger but not yet in SOCOM. Each upcoming session takes ONE and
**distils + matures** it into SOCOM canon/schemas/CLI — port the pattern, not the code.

Method per extraction (constitution §contracts-before-code, §research-first):
1. Read the Akili source end-to-end; write down the *essential* pattern (not the impl).
2. Design the SOCOM form (canon XML / schema / `socom` subcommand) — agent-agnostic, minimal.
3. Falsifiable contract before code; validate; one atomic increment.

## Ranked backlog

| # | Capability | Akili source | SOCOM today | Why |
|---|---|---|---|---|
| **1 — NEXT** | **Evals (measurement backbone)** | `evals/cycle-*.json`, `scripts/akili-graph/commands/eval*.py`, `logs/agent/ledger.csv` | nothing | gives `verify-never-claim` a scored, replayable spine |
| 2 | Lessons system | `LESSON-SYSTEM-ENGINEERING.md` | `.socom/lessons/` stub | the engine behind a feature SOCOM only gestures at |
| 3 | Assessments + precondition audits | `assessments/` (50 files), `precondition-audit.md` | only the `reviewer` role | structured adversarial assessment > one role |
| 4 | Agent introspection | `agent/extract-{assertions,beliefs,plan,reflections,skills}.sh` | none | structured self-capture → feeds memory/lessons |
| 5 | Protocol docs → canon | `docs/{SUCCESS-FAILURE-CONTRACT,INCIDENT-RESPONSE-PROTOCOL,RESIDUALITY-CONTRACTS,COMMIT-PROTOCOL,AGENT-PROTOCOL}.md` | partial (constitution/doctrine) | promote battle-tested protocols into canon |
| 6 | Contract machinery | `contracts/` (schema + examples + tests) | "contracts before code" doctrine only | make the contract a real, testable artifact |

---

## #1 — Evals (the chosen first extract)

### What Akili does (the essential pattern)
A **ledger → cycle → query** measurement spine:
- **Ledger** (`logs/agent/ledger.csv`): every agent run appends a row — role, task, exit code,
  duration, attempt number, done/failed.
- **Eval cycle** (`evals/cycle-<ts>.json`): a periodic rollup over the ledger computing
  `pass_rate`, **`pass@1`**, **`pass@k`**, per-**role** pass rates, **hotspots** (tasks that
  keep failing), **efficiency** (actual vs estimate-seconds ratio), **attempts-to-success**,
  exit-code distribution, preflight skips.
- **Query suite** (`scripts/akili-graph/commands/eval_{health,reliability,trends,failures,lessons,metrics}.py`):
  read-only analyses over the ledger/cycles — health, reliability, trends, and a `eval_lessons`
  bridge where repeated failures become lesson candidates.
- (control-plane also has `governance_policy_evaluations` — out of scope for the first port.)

### The SOCOM form to build (agent-agnostic, minimal)
SOCOM already has the *units to measure*: **seats** (roles) executing **promises** against
**contracts**, with **gates** at known bands. Evals make their outcomes scored + replayable.
1. **A run ledger** — define a `ledger.xml`/JSONL schema in `schemas/` (one row per promise
   execution: seat, promise/task id, contract id, gate band, exit code, duration, attempt,
   verdict). Append-only; lives in the repo (§git-is-source-of-truth).
2. **An eval cycle** — `socom eval` rolls the ledger into a cycle artifact: pass@1, pass@k by
   seat, hotspots (promises that keep failing assessment), contract-coverage. Distil Akili's
   cycle JSON to the SOCOM vocabulary (seats not roles, promises not tasks).
3. **A gate tie-in** — wire the cycle into `gates.xml` so `verify-never-claim` can cite a
   *measured* pass-rate trend, not just per-task prose. Failures feed lesson candidates (#2).
4. **CLI**: `socom eval [--since] [--seat] [--cycle]` (mirror the eval*.py suite, collapsed to
   one subcommand with flags), read-only, cache-free.

### Falsifiable exit (contract for the session)
- `socom eval` emits a cycle artifact with pass@1 + pass@k per seat from a real ledger; and a
  gate (`socom gate ...`) can fail/flag on a pass-rate threshold — proven on a seeded ledger.

### Source pointers
- `~/Documents/projs/Akili/evals/cycle-*.json` (the rollup shape — read 1-2 fully)
- `~/Documents/projs/Akili/scripts/akili-graph/commands/eval_*.py` (the query suite)
- `~/Documents/projs/Akili/LESSON-SYSTEM-ENGINEERING.md` (the eval→lesson bridge, also #2)
- SOCOM targets: `schemas/` (new ledger schema), `canon/gates.xml`, `bin/socom`, `socom.yaml`.
