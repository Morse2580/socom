<!-- hand-authored 2026-06-14 — supersedes the generated P-2026-06-14-main; next closeout's `socom prompt` regenerates it -->
# Next session — socom: backlog #4 (Agent introspection) — structured self-capture

You are resuming the **SOCOM substrate** (`~/Documents/projs/socom`) — the lean, agent-agnostic
governance core extracted from Akili. Standing focus (operator, 2026-06-13): each session takes
**ONE** Akili capability and distils + matures it into SOCOM canon/schemas/CLI — port the
*pattern*, not the code. Three are shipped: `socom cycle` (#1 evals), `socom lesson` (#2),
`socom precond` (#3). **#4 — Agent introspection — is NEXT.** Read
`.socom/handoffs/H-2026-06-14-main.xml` and `EXTRACTION-BACKLOG.md` before anything.

Begin by:
1. `socom gate session-start` (drift + orphan reaper + breach debt — NON-NEGOTIABLE).
2. Read `.socom/handoffs/H-2026-06-14-main.xml` end-to-end — the exit state you inherit.
3. `socom claim --scan`, then `socom claim cli` (the #4 work is a new subcommand; socom
   domains are `protocol`/`cli`/`canon` — not mwingz's platform/products/ci) before any work.
4. Load the session-start section of `.socom/memory/INDEX.md` and the lessons for the domain.
5. Non-trivial: plan mode; ratify a falsifiable contract before code (§contracts-before-code).

## Inherited state (clean — verified at generation)
- Working tree **clean**, on `main`, last commit `ef1cdb3` pushed + CI green. **No blockers.**
- The handoff's two uncommitted items (chunks.jsonl churn, `.socom/claims/`) are now resolved.
- CLI surface present and proven: `claim cycle doctor eval gate index init lesson precond prompt`.
- #3's **assessment-artifact half is deferred** (judged covered by reviewer/adversary/validator
  + `promise.<assessments>`) — do NOT pick it up unless the seats prove insufficient.

## The work — #4 Agent introspection (the chosen extract)
Akili's five post-session extractors (all at `~/Documents/projs/Akili/agent/extract-*.sh`,
**read each end-to-end first** — §research-first). The essential pattern, verified from source:

| Akili script | Fires after | Parses journal section | Distils into | Theory |
|---|---|---|---|---|
| `extract-assertions.sh` | **all** outcomes | `## Assertions` (ASSERT lines) | machine-verifiable Assertion nodes | verification regardless of done/fail |
| `extract-beliefs.sh`     | DONE | `What Was Learned` | **Provisional lessons** (append) | the belief→lesson bridge |
| `extract-reflections.sh` | FAILED | `What Failed` | structured failure reflections | mirror of beliefs, failure side |
| `extract-plan.sh`        | DONE | `What Was Done` | reusable plan template | Agentic Plan Caching (NeurIPS'25) |
| `extract-skills.sh`      | DONE | `What Was Done` | reusable skill patterns | Voyager skill library (Wang'23) |

**Invariant across all five (port this faithfully):** post-session journal parse,
*outcome-conditional*, and **every failure path exits 0 — never blocks the agent pipeline**
(this is the velocity constraint #3 also honored: warn, never stop the flow).

### The SOCOM form to design (agent-agnostic, minimal — port the pattern, not the code)
Akili targets a FalkorDB graph; **SOCOM is file-based** — the sink is the repo (memory files +
`socom lesson` candidates), not a graph. SOCOM already has the journal equivalent: the
**handoff XML** (`done`/`undone`/`warnings`/`next`) and per-session records. The port:
1. **One subcommand** — e.g. `socom introspect [handoff]` — reads the session's handoff (or a
   journal), and emits structured self-capture: belief candidates → **feed `socom lesson`'s
   candidate pipeline** (the bridge already exists from #2); failure reflections from `undone`/
   blockers; optionally plan/skill templates from `done`.
2. **Outcome-conditional + exit-0 always** — mirror Akili: capture on success AND failure, but
   never block closeout. Advisory like `precond` (§velocity — the operator's standing constraint).
3. **No new store if avoidable** — reuse `schemas/lesson.xml` + memory files. Add a schema only
   if a genuinely new artifact (assertion/plan-template) has no home.
4. **Tie to the closeout ritual** — the handoff's `next` already flags "lesson distillation in
   the closeout canon ritual" as still-open; introspection is how that becomes mechanical
   instead of recalled (recall is not trusted — §context-economy / closeout protocol).

### Falsifiable exit (draft the real contract in plan mode before code)
- `socom introspect <handoff>` parses a real closed session and emits ≥1 lesson candidate (via
  the existing `socom lesson` pipeline) on a DONE path AND a failure reflection on an undone/
  blocker path — proven on a seeded handoff; exit 0 on every failure path (assert with a
  deliberately broken input). Full smoke green; `socom doctor` clean; no canon breakage.

### Source pointers
- `~/Documents/projs/Akili/agent/extract-{assertions,beliefs,plan,reflections,skills}.sh` (read all 5).
- `~/Documents/projs/Akili/LESSON-SYSTEM-ENGINEERING.md` (the belief/lesson bridge, shared w/ #2).
- SOCOM targets: `bin/socom` (new subcommand), `schemas/lesson.xml` (reuse), `socom.yaml`,
  `.socom/canon/*.xml` (closeout ritual tie-in), `.socom/memory/` (the file sink).

## Also open (lower priority — do NOT scope-creep #4)
- Wire `precond` into session-bootstrap *guidance* (not a blocking gate — velocity); a
  `work-start` gate + `checks.precond` CI binding only if a hard pre-flight is wanted.
- Ledger **auto-append** so `cycle`/`lesson` measure real operation (still synthetic today).
- #3 assessment-artifact half — only if reviewer/adversary/validator prove insufficient.

## Scope discipline
ONE extraction this session (#4). Port the pattern, not the code. One falsifiable contract
before code, one atomic increment, gates green, push + CI-verify at closeout. Keep it
velocity-first: introspection is advisory and exits 0 — it must never block a closeout.
