# SOCOM bench — the Phase-0 pilot task set + baseline (the yardstick)

> Phase 0 of `.dev/ROADMAP.md`: *"Nothing downstream is provable without this. Pick the
> ground truth before building."* This directory **is** that ground truth — a fixed,
> committed task set and a captured baseline that every later claim diffs against.

## Why this exists

Phase 3 (`.dev/ROADMAP.md`) replaces *"the ceremony probably helps"* with measured
evidence: **does SOCOM beat a well-prompted agent + plain CI on the same work?**
You cannot answer that without a yardstick that does not move. This bench is the
yardstick:

- a **fixed task set** of 12 real, representative promises on the pilot repo, and
- a **baseline record** in the run ledger (`bench/baseline/`) — the "before" picture.

The single number it exists to move: **the fraction of the task set that completes
GREEN with ZERO human intervention**, gated by mechanical checks — not self-report.

## The pilot repo

**SOCOM itself.** Phase 3 is explicit — *"Apply SOCOM's own residuality gate to
SOCOM."* Dogfooding is the cheapest honest test: the reference implementation of
every task already lives in git history, so the A/B can revert a capability and
measure whether an agent restores it. The active domains (`socom.yaml`) are
`protocol`, `cli`, `canon`; the task set spans all three.

## The task set (`bench/tasks/`)

Twelve promises, each a schema-shaped `<promise>` (see `schemas/promise.xml`) with
an embedded **fully-auto** contract: *every* `<check>` carries a `<run>` command, so
`socom contract verify` scores the whole set on exit code with **no human in the
loop**. That is deliberate — the metric we move is zero-human-intervention green, so
the bench must be mechanically scorable end to end. Each contract also declares an
`<out-of-scope>` bound and a `<regression-surface>`, so it rates **ADEQUATE** under
`socom contract adequacy` (a green verify here is real confidence, not theater).

| Task | Domain | What it pins (the falsifiable done-ness) | Phase |
|---|---|---|---|
| B-01 build-determinism   | protocol | `build.py --check` green; `bin/socom` is the faithful build | substrate |
| B-02 xml-wellformed      | canon    | all substrate XML parses; the bench set parses | substrate |
| B-03 test-suite-green    | cli      | `tests/smoke.sh` green (unit + e2e + xml + ledger) | substrate |
| B-04 trust-boundary      | canon    | constitution names the untrusted-input boundary; scout seat exists | 1a |
| B-05 runaway-guard       | protocol | `max_runtime_s` ceiling configured + enforced | 1b |
| B-06 trace-otlp          | protocol | `socom trace` emits OTel GenAI spans | 2a |
| B-07 token-meter         | protocol | `socom meter` feeds token-real `gen_ai.usage.*` | 2a |
| B-08 judge-calibration   | protocol | `socom judge` reports TPR/TNR separately | 2b |
| B-09 lesson-regression   | protocol | `socom lesson regression` (the do-not-break gate) | 2b |
| B-10 contract-adequacy   | cli      | `socom contract adequacy --gate` passes a strong contract | 2c |
| B-11 contract-verify     | cli      | `socom contract verify`/`show` run a contract's checks | spine |
| B-12 degrade-loudly      | cli      | fails closed (nonzero) on missing / non-XML input (R6) | safety |

**Honest caveat — what this baseline is and is not.** These are *invariant-holds /
capability-present* contracts, so against the reference repo the baseline is
intentionally **all green** (12/12 kept). That all-green is not the result — it is the
*calibration*: it proves the set is well-formed, the checks execute, and the
measurement spine (verify → ledger → cycle) rolls real data. The **signal** comes in
Phase 3a, below, by perturbing the repo and watching the number fall and (maybe)
recover.

## The baseline (`bench/baseline/`)

Captured by `bench/run_baseline.sh`, which runs every task through the **real
Phase-2 spine** — `socom contract verify --record` → the run ledger → `socom cycle`:

- `summary.tsv` — the stable, diffable result (`task  verdict  exit`); **no
  timestamps**, so a content diff shows exactly which tasks moved.
- `runs.jsonl` — the frozen ledger rows (the wire format, `schemas/ledger.xml`).
- `cycle.txt` — the rolled cycle readout: pass@1, pass@k, contract-coverage.

Regenerate any time (replayable evidence):

```sh
bash bench/run_baseline.sh
```

Current baseline: **12 kept / 0 broken (pass@1 12/12, 100%)** — the reference floor.

## The A/B protocol (Phase 3a — how the yardstick earns its keep)

For a task (or a subset), measure SOCOM-on against a SOCOM-off control on the
*same* work, scored by this bench:

1. **Perturb** — revert the capability a task pins (e.g. for B-05, drop the
   `max_runtime_s` enforcement). The task now verifies **broken**: the yardstick
   has a gap to close.
2. **SOCOM-on arm** — an agent works the promise inside the substrate (constitution,
   contract-before-code, gates, handoff).
3. **SOCOM-off arm** — a well-prompted agent + plain CI works the same promise with
   no substrate.
4. **Score both** with `socom contract verify` (and roll with `socom cycle`). The
   metric: did the arm restore **green with zero human intervention**, in how many
   attempts (`pass@1` vs `pass@k`), at what token cost (`socom meter` / `socom trace`)?

Honest either way: if SOCOM-on wins you have evidence and know *which* ceremony
drove it; if it does not, you learned cheaply which ceremony is dead weight and cut
it (Phase 3b — shed scaffolding the model has outgrown).

## Conventions

- Task ids are `P-BENCH-NN`; contract ids `C-BENCH-NN`; `session="bench"`.
- Adding a task: drop a `<promise>` in `bench/tasks/`, keep the contract fully-auto
  and ADEQUATE, then re-run `bench/run_baseline.sh`. `tests/xmlcheck.py` gates the
  task set for well-formedness (a malformed promise fails pre-commit and CI).
