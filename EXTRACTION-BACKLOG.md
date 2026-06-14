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
| ~~1~~ **DONE** | ~~Evals (measurement backbone)~~ → shipped as `socom cycle` (commit c405560): `schemas/ledger.xml` + ledger→cycle rollup (pass@1/pass@k by seat, hotspots) + `eval` gate. | `evals/cycle-*.json`, `eval*.py`, `ledger.csv` | **`socom cycle`** | done — `verify-never-claim` now has a scored, replayable spine |
| ~~2~~ **DONE** | ~~Lessons system~~ → shipped as `socom lesson` (commit 116f5c1): `schemas/lesson.xml` + candidates/list/promote/retire; born from cycle hotspots (eval→lesson bridge), retrievable via existing index, retired-preserved via lifecycle filter. | `LESSON-SYSTEM-ENGINEERING.md` | **`socom lesson`** | done — the eval→lesson bridge is real |
| 3 — **precond ✓ DONE**, assessment pending | **Precondition audits** → shipped as `socom precond` (commit ea71c32): velocity-first work-readiness pre-flight (auto-heal, warn-default, block only the unrecoverable) — the "published gate" doctrine made real. **Assessment-artifact half deferred** (already partly covered by reviewer/adversary/validator + `promise.<assessments>`; revisit only if the seats prove insufficient). | `precondition-audit.md` (done); `assessments/` (deferred) | **`socom precond`** + reviewer/adversary seats | precond fills the before-bookend gap; structured assessment is optional polish |
| 4 — **assertions ✓ DONE**, LLM halves deferred | **Agent introspection** → shipped as `socom introspect` (commit bd8b7a1): `schemas/assertion.xml` + handoff `<evidence>` commands → an append-only replayable assertion log (idempotent), with a second lesson-birth path (`source="introspect"`) from captured failures. Ported the ONE deterministic extractor (`extract-assertions.sh`); the four LLM-backed halves (**beliefs/reflections/plan/skills**) are **deferred** — they need a model and would couple the substrate core to one (residuality gate). | `agent/extract-{assertions,beliefs,plan,reflections,skills}.sh` | **`socom introspect`** | done — verify-never-claim is now replayable, not quotable |
| 5 — **residuality ✓ DONE**, rest covered/deferred | **Protocol docs → canon** → shipped `residuality.xml` (commit cb00b98): the constitution §residuality-gate made falsifiable — 4 gate questions + trigger words + Saltzer & Schroeder (1975) ten principles as a fail-against checklist + an evidence shape, compiled into CLAUDE.md/AGENTS.md/.cursor + L1-indexed (16 chunks). **Non-duplication proven**: success-failure / incident-response / agent-protocol are ALREADY fully covered by the constitution (not ported); **commit-protocol deferred** (real gap, but fits socom.yaml/hooks not canon). Akili's INFRA residuality tables deliberately NOT ported (wrong bounded context). | `docs/RESIDUALITY-CONTRACTS.md` (pattern, not code) | **`.socom/canon/residuality.xml`** | done — the residuality gate is now retrievable + replayable, not just prose |
| **6 — NEXT** | Contract machinery | `contracts/` (schema + examples + tests) | "contracts before code" doctrine only | make the contract a real, testable artifact |
| 7 | commit-protocol → canon (or socom.yaml) | `docs/COMMIT-PROTOCOL.md` | structured-commits principle + commit-msg gate | per-block semantics/templates (the #5 deferred half) |

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
