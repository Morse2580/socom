# Build bucket

Work whose deliverable is **a capability**.

Governed by [`../decisions/0001-exposure-before-capability.md`](../decisions/0001-exposure-before-capability.md):
**no capability beyond R1 lands until `EV-NONAUTHOR-EXPOSURE-01` carries a
recorded result.** Every row below R1 therefore reads `BLOCKED` and names that
row as its blocker. That is not a scheduling opinion; it is §14.4 of the source
research, which the 2026-08-02 build bypassed without withdrawing.

Ladder reference: §14.2 of
`Akili:thoughts/shared/research/2026-08-01-agent-development-substrate-standalone-product.md`.

---

## Active

- `R1-INTENT-DRIFT-DETECTOR-01` **READY P0** — **Parse the repo's declared agent
  intent (`CLAUDE.md`, `AGENTS.md`, `.cursor/rules`) into checkable assertions,
  then verify each against the repo.** The only capability row permitted to
  proceed today. **Why it is the one:** it pays off to a stranger on run #1 — it
  finds lies in their *own* config, needs nobody's permission, no protocol to
  adopt, nothing to configure. That is what makes it the cheapest instrument
  ever available for moving the D-tier, per §14.4. Contrast R3, already built,
  whose payoff is structurally invisible without 2+ agents and a stock of
  findings. ✅ **[[EV-R1-ACCEPTANCE-CORPUS-01]] is DONE (2026-08-03)** — the corpus is
  committed and R1 does not exist yet, so the ordering that makes it worth
  anything is intact and is now enforced permanently by `tests/r1corpus.py`
  (git-ancestry assertion, in CI). **Read
  [`../bench/r1-corpus/README.md`](../bench/r1-corpus/README.md) §How to score
  R1 before writing a line** — it fixes what R1 is graded on, and it was fixed
  before you got here specifically so you cannot move it. Note there is
  deliberately **no recall threshold**: report recall, precision and the
  assertion count together, then argue about whether the recall is enough. ⚠️ **R1 must parse, and parsing can be wrong** — this is exactly why
  §20 preferred the blackboard, whose findings are authored and need no
  inference. Accept the inference cost here; it is the price of paying off to
  one person. ⚠️ **The referent usually still EXISTS — read this before choosing a
  mechanism (corrected 2026-08-05).** This row previously illustrated acceptance
  with *"a build command that was renamed"*, i.e. a referent that went missing.
  **That is not what the corpus grades.** Measured against `corpus.jsonl`:
  **18 of 19 defects are `subclass: paired-parent`** — the same repo, the same
  config blob, the same referent present in *both* commits, differing only in
  that the referent **was edited** between parent and defect commit, contradicting
  a rule like `"Never edit these files: docs/reference/options.md"`
  (`expected: at_defect_commit=FINDING, at_parent_commit=CLEAN`). Only **1 of 19**
  (`declared-never-existed`) is the missing-referent case. **So R1 is graded on
  history-aware contradiction, not on existence-checking.** An implementation that
  only asks "does this path/script exist" scores ≈1/19 recall and cannot pass —
  and it is also the slice already shipped by others (`giacomo/agents-lint`,
  12★, unlicensed, dormant since 2026-03; verified 2026-08-05), whereas
  git-history contradiction is that project's *unreleased* roadmap item and was
  found in no shipped tool. The existence framing pointed R1 at the taken slice;
  the corpus points it at the open one. **This also resolves the §14.2 "13% of
  576 statements name a checkable referent, actual drift ≈0" probe** — that
  measurement was existence-checking a maintained repo, which is why it found
  nothing; it is not evidence about the contradiction case.
  **Falsifiable acceptance:** on a repo whose `CLAUDE.md` declares a rule about a
  file, and whose history shows that file changed in violation of it, R1 reports a
  finding at the defect commit and reports **CLEAN at the parent commit** — the
  paired form, since a detector that fires at both has learned nothing; and it
  scores against [[EV-R1-ACCEPTANCE-CORPUS-01]]'s mined corpus on **recall,
  precision and non-vacuity together** per `bench/r1-corpus/README.md` §How to
  score R1 (`recall = defects reported / 19`, `precision = 1 − findings on the 11
  controls / 11`, `non-vacuity = assertions extracted on C01, must be ≥ 20`), with
  the per-defect result recorded — so "reported nothing" cannot be confused with
  "parsed nothing". **Report all three or none.** **Size:** 1–2 wks. **Files:**
  `src/socom/` (new module), `tests/`, `bin/socom` (rebuilt via `build.py`).

## Blocked

All blocked on [[EV-NONAUTHOR-EXPOSURE-01]] per decision 0001.

- `BUILD-ACP-RUNTIME-SEAM-01` **BLOCKED P2** — blocked on
  [[EV-NONAUTHOR-EXPOSURE-01]]. **Speak the Agent Client Protocol
  ([agentclientprotocol.com](https://agentclientprotocol.com), JSON-RPC 2.0 over
  stdio) instead of hand-rolling one vendor binding per agent — and evaluate
  whether socom's right shape is an ACP *proxy* rather than an adopted
  substrate.** Never considered: zero mentions of ACP anywhere in this repo, and
  it is not a timing excuse — ACP shipped 2025-08, ~7 months before socom
  started, and JetBrains, Google and GitHub had adopted it across 25+ agents.

  **The narrow case (the seam).** `spawn.py:83` is
  `RUNTIMES = {"claude-code": {"binary": "claude", "argv": _claude_argv, …}}` —
  one vendor, a bespoke argv builder, under a comment promising *"a new runtime
  is one entry here, never a fork of the launch logic."* **That table is a
  hand-rolled mini-ACP**: precisely the per-agent fragmentation ACP exists to
  delete, reinvented for n=1. A tool whose pitch is *"substrate for orchestrated,
  contract-bound machines"* and whose thesis is multi-agent coordination cannot
  orchestrate a second vendor without a new entry. That is a Claude Code wrapper
  wearing the word substrate.

  **The wide case as originally filed — ⚠️ REFUTED the same day; read the
  EVALUATED block below before acting on any of it. Kept verbatim because the
  refutation is only legible against the claim it killed.** It argued this was a
  candidate answer to the entry-shape problem, hence P1. ACP is editor↔agent. socom is neither, but it is a *middlebox* —
  it launches agents and governs them — and a middlebox is exactly what gets both
  interfaces free from a client/agent protocol: **the editor speaks ACP to socom;
  socom speaks ACP to the real agent; socom interposes the gates, the claims and
  the ledger in between.** In that shape socom plants **zero files**, rewrites
  **zero git config**, needs **no `.socom/`**, and works with any editor and any
  agent. Compare what a stranger currently absorbs at first contact: ~32 planted
  files and a `core.hooksPath` rewrite, which the 2026-08-04 scout assessment
  says spends first-contact trust before earning any.
  ⚠️ **It attacks the confound decision 0001 names as structural.** `0001`
  records that *"a stranger cannot evaluate 'is drift-detection useful' without
  also absorbing 'will this rewrite my git hooks' — two hypotheses, one test,
  inseparable result."* Interposition **separates them**: governance can be
  evaluated without adoption being consented to. That is the same property
  `0001` §Do-NOT already demands of R1 (*"ship it standalone — own binary, zero
  adoption, zero git-config writes, no `.socom/`"*), generalised from one
  increment to the product's entry shape.

  ⚠️ **This does NOT license building it, and does not substitute for the
  exposure.** A better front door is still a guess about a house nobody has
  entered. `0001` §2 blocks every increment beyond R1 until
  [[EV-NONAUTHOR-EXPOSURE-01]] has a result, and this row is bound by that like
  every other. Building a superior adoption model *before* one non-author has
  tried the current one repeats the exact error `0001` was written to correct —
  at one level up, which is what makes it tempting.

  **Proof tier: D0 — ASSUMED.** Nothing here has been executed. The load-bearing
  mechanism — *can socom interpose as an ACP proxy at all, preserving gate and
  ledger semantics across the hop?* — has never been run. Per the root gate, no
  contract, schema or wire format may be cut above D1, so the first action when
  unblocked is a throwaway spike against a real ACP client, **not** a design.
  ⚠️ Do not delete the git-hook layer if this ships: hooks bind the **repo**
  (any actor, including a human with no editor), interposition binds the
  **session**. They cover different populations —
  [[DEF-UNRESOLVABLE-GATE-LEAVES-NO-TRACE-01]] is what happens when a
  declaration outlives the capability that served it.

  ⚠️ **EVALUATED 2026-08-05, same day it was filed — the wide case does NOT
  survive probing, and this row was re-rated P1 → P2 as a result.** Filed on the
  claim that the proxy shape delivers *zero planted files, zero git-config
  writes*, making it a candidate answer to the entry-shape problem. Four probes
  against the tree at `b7cb1ef` refute the load-bearing half:
  1. **Enforcement does not map.** Of 8 gates, exactly 3 are git-triggered —
     `pre-commit`, `commit-msg`, `pre-push` (`HOOK_TEMPLATES`,
     `lifecycle.py:254`) — and those 3 are the ones that actually *block*. ACP
     carries editor↔agent turns and tool calls; it has no `git commit`. Gating
     agent tool-calls instead is a **different enforcement model**, not a
     transport swap, and it is blind to a human editing the same repo.
  2. **"Zero planted files" is false.** `.socom/` carries **17** state
     directories (`index`, `canon`, `gates`, `ledger`, `memory`, `lessons`,
     `handoffs`, `context`, `prompts`, `evals`, `cycles`, `claims`, `traces`,
     `runs`, `promises`, `ci`, `assertions`). Canon, index and ledger all need a
     home; a stateless proxy has none.
  3. **"Zero git writes" is architecturally impossible for the blackboard.**
     `BB_REF = refs/socom/blackboard` is pushed to the remote *by design*, so a
     teammate sees open leases. socom's multi-agent half — §20's "the part that
     measures" — requires git, and cannot be interposition-only.
  4. **Population shift, not entry-shape fix.** `PILOT.md`'s audience is Claude
     Code, whose stated path is *"paste this to Claude Code"* — a terminal
     session, not an ACP one. ACP reaches Zed/JetBrains-driven users. That is a
     different population, which may be worth pursuing but is a **pivot**, not a
     cheaper front door for the current one.

  **What survives:** (a) the narrow seam — `RUNTIMES` really is a hand-rolled
  mini-ACP and replacing it is a genuine bounded win (~3 d); (b) a *hybrid*, far
  narrower than filed: proxy the **session-scoped** half (context injection, run
  ledger, seat dispatch) and keep git hooks for the **repo-scoped** half. That
  maps onto the hooks-bind-the-repo / interposition-binds-the-session split
  already noted below — but it explicitly does **not** deliver zero-adoption,
  which was the entire reason this was rated P1.
  **What does not survive:** the claim that this separates `0001`'s two
  hypotheses. The cheap mechanism for that is already filed and already READY —
  **ship R1 standalone**. This row is not a substitute for it.
  *(Recorded because the first framing of this row was advocacy that had not been
  probed. `[[clean-runs-on-a-degenerate-input-are-not-evidence]]` applies to
  arguments too: an unprobed case is most confident exactly where it was never
  exercised.)*

  **Watch for it in the exposure run, free:** if the participant drives Cursor,
  Codex or Gemini CLI rather than Claude Code, record what happens when they meet
  the seat/runtime config (§4 of `bench/exposure/TEMPLATE.md`). That observation
  costs nothing and is worth more than the feature.
  **Falsifiable acceptance:** socom governs a session driven by an agent that has
  no entry in `RUNTIMES`, with the gate and ledger semantics of a native run, and
  with zero files planted and zero git config written in the target repo.
  **Size:** ~3 d for the narrow seam (the part that survived evaluation); 2–3 wk for the session-scoped hybrid. The full zero-adoption proxy is NOT scoped — it was refuted.

- `R2-CLAIM-VERIFIER-HOOK-01` **BLOCKED P2** — commit/PR hook refusing claims
  that lack evidence: "tests pass" with no captured run, "verified" with no
  output. Turns verify-never-claim from a principle into a gate on your own
  commits, solo. **Falsifiable acceptance:** a commit asserting a green suite
  with no recorded run is rejected; one with a captured run passes. **Size:**
  1 wk.
- `R4-HANDOFF-COMPILER-01` **BLOCKED P2** — session end emits a structured
  handoff derived from what actually happened (diff, gates run, commands,
  outcomes), not authored by hand. **Falsifiable acceptance:** the handoff
  regenerates deterministically from git + run records with no human input, and
  a resumed session reaches the same working state. **Size:** 2 wks.
- `R5-THE-RECORD-01` **BLOCKED P3** — the typed store: provenance, contradiction,
  temporal validity, decay — written as a side effect of R1–R4, queryable on
  demand. **Deferred by design, therefore last** — its value is the most
  deferred and most plural, and starting here is what killed every prior
  attempt. R1–R4 populate the store before it is built, which removes the
  cold-start problem. **Falsifiable acceptance:** a question answerable only
  from accumulated history ("why was X rejected?") returns the right prior
  decision with its provenance chain. **Size:** 3–4 wks.

#### From the 2026-08-03 cold-run cohort

Filed `BLOCKED` because each **adds a surface that does not exist today** — the
line decision 0001 §Amendment 1 draws between a repair and a capability. Their
repair-shaped halves are already filed in
[`defects.md`](defects.md); what remains here is the part that is new.

- `SUBSTRATE-CLAUDEMD-COEXIST-01` **BLOCKED P1** — blocked on
  [[EV-NONAUTHOR-EXPOSURE-01]]. **A repo with a hand-written `CLAUDE.md` has no
  adoption path that keeps it.** `adopt` correctly REFUSES to clobber it
  (verified byte-for-byte by a cold-run agent) — but then `doctor` reports
  `✗ CLAUDE.md: no socom:generated header — hand-written or tampered` forever,
  and there is **no merge / include / append mechanism**, only `--force`. The
  steady state offered is: overwrite the conventions you already own, or carry a
  permanent red. For a tool whose stated audience is *"built for Claude Code"*
  (PILOT.md), a hand-written `CLAUDE.md` is the **modal case, not the edge**.
  p2's *"I don't know what I'm supposed to do here"* is a stall point — precisely
  the output [[EV-NONAUTHOR-EXPOSURE-01]] exists to collect, which is a second
  reason not to pre-empt it. ⚠️ **Capability, not repair:** an include/merge
  mechanism does not exist and is larger than several recorded candidate
  increments. **Falsifiable acceptance:** a repo with a hand-written `CLAUDE.md`
  adopts, keeps its content, and reaches `doctor` clean. **Size:** 1 wk.

- `R3-LEASE-IDENTITY-DURABLE-01` **BLOCKED P2** — blocked on
  [[EV-NONAUTHOR-EXPOSURE-01]]. **Lease identity is ambient process state, so
  leases orphan and ownership is spoofable.** VERIFIED at `blackboard.py:93`:
  `SOCOM_SESSION or f"{gethostname()}-{os.getppid()}"`. PPID is the parent shell,
  so identity churns across invocations — two consecutive calls on this box gave
  `akili-build-2027022` then `…2027320`. 4/5 agents orphaned their own lease;
  `cmd_release` has no `--force` or steal (`grep force|steal` → no matches), so an
  orphan is unbreakable for the full 8h TTL short of hand-editing JSONL. And
  `SOCOM_SESSION=<id-read-from---scan> socom release --all` releases a lease it
  does not own — `--scan` hands out the key.
  **Scope, corrected twice and now measured:** the MCP path is a persistent stdio
  server (`mcp.py:343`), so identity is stable **within one server process** — but
  it is re-derived on every server start, and a live restart experiment showed the
  lease orphaned to a dead identity, `release --all` returning `released: []`, and
  re-claim refused. Akili's `.mcp.json` sets **no** `SOCOM_SESSION`, so Akili is
  exposed per-restart. (Its one lease shard, `akili-build-1090626.jsonl`, carries
  its own `release` record 23 min later — exposed to the mechanism, not yet bitten.)
  ⚠️ **Capability, not repair:** "a session cannot release a lease it does not own"
  is an **authorization mechanism that does not exist today**, on an instrument
  decision 0001 demoted. **Falsifiable acceptance:** a lease taken in one
  invocation is releasable from another on the same machine, and a session cannot
  release a lease it does not own. **Size:** 3–5 d.

- `SUBSTRATE-STATUS-TIER-SWEEP-01` **BLOCKED P2** — blocked on
  [[EV-NONAUTHOR-EXPOSURE-01]]. **Extend the `verified`/`asserted` tier discipline
  socom already derives for findings (`blackboard.py:508`, citing arXiv 2310.01798)
  to what socom says about itself** — changing what the seven status surfaces
  derive their claims *from*, not merely labelling them. Requires a band-outcome
  record that does not exist: the ledger has no `blocked` field, and rows are
  written only by `gate task-completion <promise.xml>` and `contract verify
  --record` — both of which deliberately refuse promiseless rows citing
  `§separation-of-privilege` (`gate.py:87`, `ledger.py:325`). Routing plain
  `pre-commit`/`pre-push` through it means relaxing a fail-closed identity
  contract and filtering four downstream consumers (`retrieval.py` pass@k,
  `monarch.py` recovery eligibility, `lesson.py`, `value.py`) so the new rows do
  not corrupt them. Six files plus a schema. **Prerequisite:**
  [[DEF-LEDGER-GATE-BAND-HARDCODED-01]] — the band must be true before anything is
  derived from it. The **labelling** half is [[DEF-STATUS-CLAIMS-UNLABELLED-01]].
  **Falsifiable acceptance:** on a repo where an amber gate fired and the commit
  landed, `socom value` does not say "stopped before they landed", and a RED
  pre-push block appears in the count. **Size:** 1 wk.

- `SUBSTRATE-COMMIT-TYPES-CONFIGURABLE-01` **BLOCKED P3** — blocked on
  [[EV-NONAUTHOR-EXPOSURE-01]]. **Make the commit-type allowlist configurable in
  `socom.yaml`.** VERIFIED there is no knob today: `COMMIT_RX` has exactly two
  occurrences repo-wide — its definition (`gate.py:62`) and its single use
  (`gate.py:112`). ⚠️ **Capability, not repair** — a new config surface. The
  repair (widen the set, print the rule) is
  [[DEF-COMMIT-GATE-REJECTS-HOST-CONVENTION-01]] and needs no new surface.
  **Falsifiable acceptance:** a repo declares its own commit types in
  `socom.yaml` and the gate enforces that set. **Size:** 2 d.

### Candidate increments — recorded, unscheduled

Full text in [`../ROADMAP.md`](../ROADMAP.md) §Candidate increments. All
`BLOCKED` on [[EV-NONAUTHOR-EXPOSURE-01]]. Each is larger than the artifact that
already failed with zero users: lease-holder invalidation via `notifications/*`
· projection to a queryable store · streamable HTTP transport · findings graded
by repo outcome · autonomous spawn on a blackboard trigger.

## Done

- `R3-BLACKBOARD-01` **DONE** (`2b8f244`, 2026-08-02) — `claim` / `attest` /
  `findings` / `resolve` / `release` over a local stdio MCP server; append-only
  JSONL, one shard per author, synced over `refs/socom/blackboard`. Works, is
  tested, and is in live use from Akili sessions. **Recorded honestly:** this
  was built out of ladder order. §14.4 said ship R1 alone and build nothing
  beyond it until the non-author measurement exists; §20 said build this first;
  the build followed §20 and §14.4 was never withdrawn. Decision 0001 resolves
  that in favour of §14.4 and **demotes this from "the experiment" to "an
  instrument."** It is not being reverted — it is built, it is not in the way,
  and deleting it would be motion rather than progress. **What it does not
  establish:** anything about adoption by a non-author, which is the claim
  actually at D0.
