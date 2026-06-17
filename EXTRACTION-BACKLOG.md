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
| 6 — **verify ✓ DONE**, followups deferred | **Contract machinery** → shipped `socom contract verify`/`show` (commit 1b33918): EXECUTES the `<check><run>` commands a promise already embeds (schemas/promise.xml) — PASS/FAIL on exit code, no-run checks flagged MANUAL (fail-closed, never auto-passed). New `schemas/contract.xml` (schema-by-example). The Akili conformance-runner pattern, collapsed to one verb. **Reframe**: SOCOM already HAD the contract; #6 made it executable, not a new notion. **Followups deferred** (#6f): standalone `.socom/contracts/` storage + lifecycle; §R10 renegotiation; record verify → assertion-log (#4 bridge) / ledger; per-contract pass@1/pass@k in cycle. | `contracts/` (pattern, not code) | **`socom contract`** + `schemas/contract.xml` | done — the contract is now testable, not inert |
| 7 — **canon ✓ DONE**, scaffold deferred | **commit-protocol → canon** → shipped `commit-protocol.xml` (commit 11ad743): the per-block semantics of SOCOM's existing six commit blocks `[what][why][how][test][broke][next]` + Akili's discipline (journey / verbatim-errors / dead-ends / one-logical-change / verification / grep-the-journey) ported as the teaching layer, compiled into CLAUDE.md + L1-indexed (13 chunks). **Port the pattern, not the block names**: SOCOM keeps its six (gate + constitution depend on them); this DOCUMENTS their meaning, it does not restructure them. Gate left ADVISORY on the four soft blocks (velocity-first). **Scaffold half deferred** (#7b): `.gitmessage` template via compile + `git config commit.template` — chosen against here because it touches machine-local git config (not git-source-of-truth, won't propagate to clones) and the gap was documentation. | `docs/COMMIT-PROTOCOL.md` (pattern, not code) | **`.socom/canon/commit-protocol.xml`** | done — the six blocks' meaning is now retrievable + compiled, not folklore |
| 7b | Commit-protocol operational scaffold | `docs/COMMIT-PROTOCOL.md` (the format block) | `commit-protocol.xml` (the docs) | `.gitmessage` emitted by `socom compile` + `git config commit.template`; prompts the six blocks at write time. Only if the operator wants the scaffold — the canon docs already close the meaning gap. |
| 6f — **ledger auto-append ✓ DONE** (both producers), rest open | Contract machinery followups. **Two automatic run-ledger producers shipped, closing the long-open auto-append gap.** (1) `socom contract verify --record` (commit 927905d): on-demand — a fully-mechanical verify of a promise appends one `.socom/ledger/runs.jsonl` row. (2) `socom gate task-completion <promise>` (commit 84e99e4): BY DEFAULT — the done-gate an agent already runs records its verdict (kept iff the bound check passed), the canonical "a gate assessed the promise" event. One shared writer `_append_ledger_row` (9-key wire contract, `socom cycle` round-trips both), pure `_ledger_row`/`_next_attempt`/`_promise_ref`. Fail-closed (§separation-of-privilege): standalone / manual-pending / zero-auto-check / unbound-gate all WITHHELD — the mechanical runner never records a verdict it cannot claim. cycle/lesson now measure REAL pass@1/pass@k instead of synthetic fixtures. **Rest still open** (#6f-3): per-contract pass@1/pass@k in cmd_cycle; standalone `.socom/contracts/` storage + lifecycle; §R10 renegotiation. | `contracts/` | **`socom contract verify --record`** + **`gate task-completion`** | the ledger auto-append gap is CLOSED: real data feeds cycle on demand AND at the done gate |

---

## Maintenance debt (not extractions — surfaced by drift scan)

- **CI runner Node-20 deprecation** (flagged by CI annotation on run 27509263690,
  2026-06-14). GitHub forces Node-20 actions to Node-24 by **2026-06-16**, removes
  Node-20 from runners 2026-09-16. The compiled workflow pins `actions/checkout@v4`
  + `actions/setup-python@v5` (Node-20). Fix at the ROOT, not the compiled view:
  bump the action versions in `bin/socom`'s CI-adapter template (cmd_compile, the
  `.github/workflows/socom-gates.yml` generator), then `socom compile`. Low urgency,
  hard deadline 2026-06-16.

## Initiative: install hardening + residuality self-violations (scout audit 2026-06-17)

Triggered by operator: "hwo cna thi sbe nstall'e by any dev from git" + "are there
things we have completely missed" + "have all resiudality gates been croseed off". A
scout audit found the substrate failing its OWN residuality gate on two shipped
surfaces, and the any-dev-from-git story real-in-CLI but undocumented/not-one-command.
Objective: close the class "the substrate ships surfaces that fail its own gate / can't
be cleanly adopted from a clone." Each row leashed with an ID (§no-quick-fixes-without-a-leash).

- **IH-1 — SessionStart hook portability ✓ DONE** (commit 1970622): the generated
  `.claude/settings.json` baked a machine-specific absolute path, so a fresh clone's
  session-start gate silently never fired. Routed it through the SAME `HOOK_RESOLVER`
  the git hooks use (command -v socom → $SOCOM_HOME → fallback → degrade exit 0); +3
  smoke checks. The substrate stops failing its own open-design / fix-the-class gate.
- **IH-2 — ledgercheck schema gate ✓ DONE** (this session): the JSONL run ledger
  (`.socom/ledger/runs.jsonl`) — the #1/#6f measurement spine — was validated by
  NOTHING (`xmlcheck` is XML-only; `cycle` only caught JSON-decode errors). A row that
  was valid JSON but schema-invalid (missing `verdict`, `gate_band:"purple"`) silently
  mis-scored the `eval` gate. Added `tests/ledgercheck.py`: parses the field contract
  (8 required keys + 2 enums + 3 int-typed, bool excluded) straight FROM
  `schemas/ledger.xml` — single source, no hardcoded list — and fails any bad row;
  absent ledger PASSES (fail-open on absence, fail-closed on corruption). Wired into
  medium+full+CI (all 3 adapters, via `socom compile`, not by hand). +5 smoke checks;
  independent reviewer ACCEPT (8/8 contract checks + adversarial probes clean). Closes
  the unguarded-spine residuality violation at the root.
  NOTE: CI is single-sourced from `socom.yaml` via `compile` (the feared
  full-check duplication across adapters does not exist) — no new backlog item needed.
- **IH-3 — adopt one-shot + auto-wire hooks + README ✓ DONE** (this session):
  `git config core.hooksPath .githooks` was only PRINTED (auto-healed only inside
  `precond`), so a fresh clone's LOCAL git gates were dormant until something healed
  them; there was no one-command adoption and README had no install section. Shipped
  `socom adopt` (init → compile → wire hooks → report rung), idempotent, composing the
  existing steps so it can never drift from init/compile. The `.githooks` wiring truth
  was a bare literal in 5+ places — factored into a `HOOKS_DIR` constant + a single
  `_wire_hooks` writer; doctor/precond/adoption_rung now route through it (only ONE
  `core.hooksPath` write site remains). Non-git dir warns (CI re-asserts), never
  crashes. README "From a clone" with BOTH paths (socom installed separately + in-repo
  `./bin/socom`). +7 smoke checks; independent reviewer ACCEPT (8/8 + probes clean).
  Closes the dormant-gates class at the root.
- **IH-4 — ledger concurrency (OPEN, latent)**: `_append_ledger_row` does
  read-all-then-append with no `flock`/lockfile; two seats recording at once → lost/
  interleaved row + `_next_attempt` race. Multi-agent is the stated goal — add a lock
  before two seats ever write. Pairs with the `chunks.jsonl` committed-churn decision
  (gitignore + rebuild, or deterministic ordering).
- **IH-5 — version/upgrade path, borrowed from GSD (OPEN)**: a vendored `.socom/` is
  frozen at adoption; no `socom update` to re-pull tool canon + reconcile local canon
  edits. `doctor` already has the hash-divergence detector (the seed) — promote it into
  `socom update`. Borrow GSD's version-and-reconcile half; keep compile-from-source (do
  NOT adopt copy-everywhere).
- **IH-6 — secrets/PII redaction mechanism (OPEN, lower)**: §verbatim-protocol says
  "redact before any substrate write" but no command scans handoffs/promises/ledger for
  credentials. `index`/`hydrate` already have `SECRET_RX` (HR6) — extend it to a write-
  time gate on handoffs.

## Initiative: substrate self-maintenance — `bin/socom` quality

Distinct from the Akili-extraction track. Triggered by operator: "the bin for socom py is
not good quality code … just one monolithic script". **Analyst telemetry (read-only, this
session) reframed the diagnosis**: the problem is NOT the single file.

- The file is **91% IO by SLOC**; the pure unit-testable core is only **~137 SLOC / 16 helpers**.
- **Single-file is deliberate + load-bearing** — `TOOL_ROOT = Path(__file__).resolve()…` (L60)
  resolves through the install symlink and is baked into every repo's generated git hooks
  (L313). A naive split into a package is a **one-way door** on `socom install` (residuality.xml).
- The real debt: (a) **untested pure core** — BM25/overlap/hash math had 0 direct assertions;
  (b) **structural duplication** — `root / ".socom" / …` inlined **52×**, `sys.exit` re-rolled
  **45×** (no `die()`), `datetime.now(tz)` stamped **13×** in 3 shapes; (c) **3 hotspots** —
  `cmd_cycle` (152 lines, **cyclomatic 61**, a 4× outlier), `cmd_gate` (CC 39), `render_body` (CC 23).

Residuality-ordered increment ladder (tests FIRST, then refactor under the net):

| # | Increment | State |
|---|---|---|
| SM-1 | Unit-test the pure core (`tests/unit.py`, 28 assertions, chained into smoke + CI) | **DONE** (commit cd01bfe) |
| SM-2 | Utility layer: `SOCOM_DIR` constant (52 path-builds) + `_now_iso()` (9 stamps). **`die()` residuality-REJECTED** — 45 sys.exit calls have inconsistent prefixes + all-different messages; a wrapper relocates style and risks changing smoke-grepped error text (lateral, not stress-removing). | **DONE** (commit eb7f490) |
| SM-3 | Decompose hotspots. **`cmd_cycle` (CC 61, the 4× outlier) DONE** (commit b9400bf): extracted pure `_cycle_rollup`, cmd_cycle 152→80 lines, +14 white-box rollup unit tests. `cmd_gate` (CC 39) + `render_body` (CC 23) are far below the outlier — optional follow-up, decompose only if they bite. | **cmd_cycle DONE**; gate/render_body optional |
| SM-4 | Internal package **+ bundler emitting the single file** — ONLY if SM-2/3 don't resolve navigation; a gated one-way door, defer until proven necessary | deferred |

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
