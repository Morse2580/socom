# 0007 — Adopt the sensor contract, not the sensor

**Status:** **Proposed — BLOCKED on §5.** Written 2026-08-10 against `531efc6`,
at operator request, from four external sources. **Nothing here may be built
before [[EV-NONAUTHOR-EXPOSURE-01]] §5 has a result** (`0001` §Falsifiable
acceptance). This record exists so the analysis is not re-derived, not so it is
executed.
**Rows:** [[BUILD-ACP-RUNTIME-SEAM-01]] is untouched by this.
[[DEF-STATUS-CLAIMS-UNLABELLED-01]] is named below and **stays READY P1**.
**Governed by:** [`0001`](0001-exposure-before-capability.md) —
exposure before capability. Every item below is capability.
**Upstream:** [`0004`](0004-two-boundaries-socom-does-not-represent.md) Class A
(socom reports what it wrote, not what took effect) is the boundary this
decision is about. [`0003`](0003-no-standard-binds-a-fork.md) is the precedent
for how this repo treats external material: **read it, record the verdict, adopt
nothing.**

---

## Objective, in root form

**Decide what socom takes from the 2026 harness-engineering literature, given
that socom deliberately owns no execution environment and every source does.**

Not: "add sensors." That is the instance, and it is the wrong half.

---

## Step 0 — Data breakdown

A design sentence may rest only on `MEASURED`. External claims are tagged
`EXTERNAL` and are **not** evidence about socom — see §"What this does not
claim".

| # | Claim | Tag | Probe |
|---|---|---|---|
| 1 | socom's gate result is a bare integer; check output is inherited to the terminal and never captured | `MEASURED` | `src/socom/gate.py` `run_check` — `subprocess.run(cmd, shell=True, cwd=root).returncode`, no `capture_output` |
| 2 | Every gate binds to a key in the adopter's `socom.yaml`; socom ships no check of its own | `MEASURED` | `canon/gates.xml` — 7 gates, `<binding check="checks.fast|medium|full|eval|ci.status"/>`; two are `none — built-in` |
| 3 | socom's own `ci` gate — the one canon calls "the incorruptible floor" — is bound to a placeholder in socom's own repo | `MEASURED` | `socom.yaml` → `ci: status: 'echo ''bind me: cache-free pipeline state query'''` |
| 4 | socom already stores per-rule rationale, written for agent consumption | `MEASURED` | `canon/*.xml` = 786 lines; `embed="true"` descriptions on every gate |
| 5 | socom already runs an artifact-scoped structured finding store that survives sessions and machines | `MEASURED` | `attest` / `findings` / `resolve --verdict retracted`; `blackboard.ref: refs/socom/blackboard` |
| 6 | The one recorded exposure run stalled because a bound command did not exist on the machine | `MEASURED` | `bench/exposure/2026-08-07-akili.md` §2 — `gate fast` → `RED — checks.fast failed (rc=127)`, `cargo: not found` |
| 7 | socom bounds wall-clock and bounds blocking, but bounds no retry count | `MEASURED` | `socom.yaml` `limits.max_runtime_s: 3600`; `canon/gates.xml` bands amber/red; no attempt budget anywhere |
| 8 | Böckeler's `sensors-cli` returns a typed payload: `findings[]`, `metrics[]`, `guidance[]`, `score` + direction, `success`, `summary` | `EXTERNAL — README-level only` | github.com/birgitta410/sensors-cli README, fetched 2026-08-10. **Source not read.** Re-probe against the code before binding anything to this shape |
| 9 | Stripe caps agent iteration at most 2 CI runs, then stops | `EXTERNAL` | stripe.dev/blog/minions-…, fetched 2026-08-10 |
| 10 | OpenAI shipped ~1M lines in 5 months with no hand-written source, on Codex + owned CI | `EXTERNAL — secondary source` | openai.com/index/harness-engineering/ **returned HTTP 403**; read via infoq.com/news/2026/02/openai-harness-engineering-codex/. Primary not read |
| 11 | All four sources' harnesses sit on an execution environment their authors control (devbox / Codex cloud / local daemon+socket) | `EXTERNAL` | all four, 2026-08-10 |
| 12 | Whether structured gate output changes what any participant does | **`UNMEASURED`** | needs §5, then a run. This is the whole premise and it is untested |
| 13 | Whether the rc=127 class recurs at all outside `n=1` | **`UNMEASURED`** | one sighting, one machine |

---

## The finding that reorganises the rest

Böckeler's split is **guides** (feedforward — steer before acting) versus
**sensors** (feedback — observe after, enable self-correction).

Against that vocabulary socom is **near-total guide with an empty sensor
socket**. Its canon compiles rules outward (`CLAUDE.md`, `AGENTS.md`,
`.cursor/rules`, `.githooks/`); its gates supply wiring and zero signal (claim 2).
socom does own sensors — `doctor`, `baseline`/`eval`, `cycle`, `judge` — but
every one is pointed at socom's own artifacts, not at the adopted repo's code.

**The load-bearing asymmetry is claim 11.** Stripe, OpenAI and Böckeler each
bought the execution environment first and layered protocol on top. socom's bet
is the inverse: protocol over participants, one curl'd stdlib file, no daemon,
no host, portable anywhere. Nobody in the field made that bet. Claim 6 is the
price of it — socom named a command and had no way to guarantee it existed.

That is either the underserved position or the position everyone else evaluated
and skipped. **No article can settle it. §5 is closer to settling it than any of
them.**

---

## Decision — what is adopted, in order, AFTER §5

Ranked by value per unit of constraint violated. Constraint: single-file stdlib
Python, curl-installable, no daemon, no third-party dependency, offline.

**1. The gate result contract.** Replace the bare integer (claim 1) with a
typed result — `findings[]`, `metrics[]`, `guidance[]`, `score` + direction,
`success`, `summary` (claim 8). Costs no dependency; it is a JSON shape, and
claim 5 says socom already runs the store it belongs in. The payoff is the one
nothing in the literature can do: **a gate finding becomes a blackboard
finding**, attached to the artifact, delivered to whoever claims it next, on
another machine, next week. Every source's findings die with their run. This is
also the direct attack on `0004` Class A — a `score` with a direction is a
statement about effect, where `✓` is a statement about what socom wrote.

**2. `guidance[]` — rationale attached to the failing rule.** Böckeler's
specific finding is that the message must teach the agent *why* the rule exists
and *how* to resolve it, including licence to judge whether a suppression is
warranted. Claim 4 says socom already wrote that content and simply never
attaches it to a red band. Wiring, not authorship.

**3. A bounded attempt budget.** Claim 7: socom caps seconds and caps blocking,
never attempts. Stripe's cap (claim 9) exists because unbounded retry is how
unsupervised agents spend money producing worse output. socom already owns the
`handoff` primitive to hand off *to*, which is the half Stripe does not have.

**4. Probe the binding before asserting it — NOT AUTHORISED, and not by §5
either.** Resolving a bound command's executable before printing `✓ gates now
run YOUR tests` is the only substitute for the devbox available under socom's
constraints. **It is also [[DEF-STATUS-CLAIMS-UNLABELLED-01]], which is READY P1
on purpose**: `PILOT.md` asks the participant *"did a metric mislead you?"*, so
repairing it deletes the finding the sheet exists to collect (`0001` §Amendment
1 rule 3). The 2026-08-07 run generated exactly that finding, which is the rule
working. **This item's hold outlives §5** and is lifted only when the exposure
instrument stops asking the question.

## Decision — what is refused

- **The sidecar shape.** `sensors-cli` needs `uv tool install`, a background
  service and a Unix domain socket (macOS-tested). Binding socom to it ends the
  30-second `curl` preflight. This is the same argument that already refuted the
  React/Ink rewrite: a change proposed to make adoption calmer that deletes the
  install story.
- **Shipping concrete sensors** — eslint, ruff, mutation testing, dependency
  rules. Language-specific, and socom's claim is substrate-not-stack. **Bind
  them; never vendor them.** Item 1 is precisely the seam that makes binding
  them worth something.
- **The devbox.** Not adoptable. It is capital, not code, and buying it would
  invert socom's premise rather than extend it.
- **MCP tool sprawl.** Stripe's 400+ internal tools answer Stripe's problem.
  `socom mcp` already serves the blackboard; nothing to take.

## What is already ahead, and needs nothing

OpenAI's prescription that documentation be the single source of truth,
mechanically enforced by linters and CI, is **already shipped here and shipped
harder**: `doctor` detects canonical-vs-compiled drift, `build.py --check` is a
CI gate, and `prompt-verify-pass` claim-verifies the next-session prompt against
the repo. Their version also cannot express *"that was never true"* —
`resolve --verdict retracted` exists for exactly the failure their docs-as-truth
model has no record type for.

---

## What this decision does not claim

- **None of the four sources is evidence about socom.** They are evidence that
  the *problem* is real and that three well-resourced teams solved it by owning
  the machine. Per `0003`'s precedent, corroboration of a principle is not a
  measurement of this tool. Claim 12 is the premise of items 1–3 and it is
  `UNMEASURED`.
- **It does not amend `0001`'s ordering.** The four sources all invest in
  enforcement (structural tests, linters, CI as the real door) and none in
  detecting stale instruction files — which is the R1 scout finding arriving
  from a fourth independent direction. **Amending `0001` remains an operator
  decision, and this record does not make it.** The standing counter-argument
  is unchanged: nobody has used the gates either.
- **It does not set the proof tier**, and does not unblock `buckets/build.md`.
- **It does not license item 4**, in this session or the one after §5.

## Trigger

Reopens when §5 of `bench/exposure/2026-08-07-akili.md` is filled, on or after
2026-08-14. A §5 answer of *"never ran it again"* closes
[[EV-NONAUTHOR-EXPOSURE-01]] and makes items 1–3 moot rather than ready — a
richer gate result for a tool nobody returns to is the exact failure mode
`0001` was ratified to prevent.
