<!-- socom:generated v=0.1 source=6e5595b1343e — do not edit; edit .socom/ + socom.yaml, then `socom compile` -->
# socom — SOCOM substrate

Protocol over participants: the rules below bind every participant — agent or human. Canonical source: `.socom/` + `socom.yaml`.

## Constitution (Non-Negotiable)

### 1. Verify, never claim

No task is done until concrete proof is shown. "It should work" is a
violation: run the check, paste the output. Evidence from a different
session, or from before the final change, does not count — re-run after the
last edit. Evidence is replayable, not quotable: record the command and exit
code, not just the prose. If verification is impossible from here, state
explicitly what remains unverified and who must check it.

### 2. Contracts before code

The validation contract — falsifiable acceptance checks with named assessors
— is written and ratified before implementation begins. Tests confirm
contracts; they are never retrofitted to bless whatever was built. A worker
cannot amend its own contract; renegotiation goes back to the originator and
is deliberately cheaper than bypass. Research-shaped work uses an exploration
promise: contract the question and a timebox, not an artifact.

### 3. Research-first

Plan before coding for anything non-trivial: multi-file, architectural,
unfamiliar systems, unclear root cause. Prefer official docs, upstream
repositories, and specifications over guessing; never rely on unverified
forum answers. Store what you learn — memory or runbook — so research is
never repeated.

### 4. Initiative framing — fix the class, not the instance

Every initiative's objective is to make an entire class of problem
structurally impossible at the root — never to patch the visible symptom.
State objectives in that form first: "eliminate class X by changing Y at the
root." When something is live and broken: mitigate the instance fast, but the
objective remains the class, same session.

### 5. Residuality gate

Before proposing any fix or hard-to-reverse decision, run the 60-second
adversarial check: does this relocate stress rather than remove it? hide a
quantitative assumption? patch a symptom instead of the class? open a one-way
door? Trigger words that demand the gate: pin, bump, raise the limit, add a
retry, add a buffer, bigger node, works for now, temporarily, good enough.

### 6. Git is the single source of truth

No manual change to a live system that is not first — or same-session —
declarative in git. Temporary live patches reconcile in the same session; a
break-glass without same-session reconciliation is itself a new P0.
Operational state (tasks, handoffs, memories, lessons) lives in the repo:
any clone on any machine has the full state. Drift is a P0.

### 7. Mitigate before perfect

Outage time is a first-class cost. Rapid read-only diagnosis, then the
narrowest possible mitigation, then the permanent class-level fix — in that
order, in the same session. Do not delay live recovery to design the ideal
solution.

### 8. Context economy

The primary's context is the scarcest resource. Offload bulk, mechanical,
and fan-out work to subordinate seats whose success is verifiable from
output (a count, a diff, a passing check). Retain judgment and final
verification in the primary — assessment is never delegated to the promiser.

### 9. Verbatim protocol

Every brief to another participant opens with the originating human's words
verbatim — typos preserved, they carry signal — followed by the decoded
interpretation, clearly labeled, so the recipient can compare the two and
flag drift. Never verbatim credentials or personal data; redact before any
substrate write.

### 10. No quick fixes without a leash

Every change must be one you would accept in the codebase a year from now.
An unavoidable shortcut gets three things: a documented why, a follow-up
task with an ID, and a TODO carrying that ID. A shortcut without a leash is
a violation, not a pragmatic call.

### 11. Structured commits

One commit format, enforced by hook: `type(scope): description` followed by
`[what] [why] [how] [test] [broke] [next]` blocks. Write full blocks on the
first branch commit — squash merges inherit it. The [test] block carries the
verification evidence; an empty [test] block is a verify-never-claim
violation in writing.

## Session protocol

### Bootstrap

1. Fetch + fast-forward main. Create an isolated worktree — never work in
   the shared checkout. Run the orphan reaper (expired claims, dead
   worktrees, handoff-less sessions).
2. Discover the latest next-session prompt AND run the drift scan — the
   prompt states what was true at write time; the repo states what is true
   now. Surface every mismatch before planning.
3. Claim the work: register the promise against a bucket row and its
   contract.
4. Load the retrieval map's session-start section and the lessons for the
   task's domain.
5. Non-trivial work enters plan mode; the plan is ratified against the
   contract before any code.

### Build

Contract first if none exists. Implement; run the fast gate after every
change. Dispatch seats with verbatim briefs; builder and reviewer never
share context. Run the residuality gate before any fix lands. Capture
memory/lesson candidates as they occur — distillation happens at closeout,
recall is not trusted.

### Closeout

One uninterrupted pipeline: bucket rows flipped to reality → push → CI
verified green → handoff written (done / undone / commands / exit codes /
blockers / warnings) → next-session prompt generated then claim-verified →
memory distillation (cap 2, five gates) → claims released, worktrees
removed, clean process table.

## Doctrine — named thinking devices (teaching layer)

Reach for the concept when its trigger fires; full text in `.socom/canon/doctrine.xml` (and via retrieval).

| Concept | Fires when | Essence |
|---|---|---|
| **Capability ladder** | Scoping any initiative; answering "what's next" at session start; suspecting false-done. | One capability per initiative, one falsifiable exit per capability, tiers per increment: T0 substrate missing → T1 present but not wired → T2 wired but not tested → T3 tested but not shipped → T4 shipped but not adopted. |
| **Initiatives and increments** | Breaking an objective into sessions of work; sizing what one session may promise. | An initiative carries one falsifiable goal and a single success metric — "fix class X at root Y" form (constitution §fix-the-class). |
| **Unison — never compromise one part to fix another** | Any fix spanning systems or layers; before implementing a ratified design; when a green check feels too easy. | Every session moves the system forward in unison: a change that fixes its target while fragmenting the whole fails, even when its code is clean, reviewed, and verified. |
| **Ratified ≠ implemented; implemented ≠ accepted** | Closing any phase, task, or fix; reading a design doc that says "X happens"; inheriting a prompt's claims. | Two distinct gaps, both fatal to trust. |
| **Design-artifact set — the ready-to-start gate** | Any work spanning more than one layer or component; before dispatching builders. | No implementation begins until the artifact set exists: solution design, implementation design, diagram, and contract — design-reviewed and operator-ratified. |
| **Bounded context and ubiquitous language** | Organizing domains; naming things; deciding where work or data belongs; noticing the same word meaning two things. | A domain is a DDD bounded context: a boundary inside which every term has exactly one agreed meaning (the ubiquitous language) and one owning team. Boundaries are structural, not tags — things do not migrate casually across them, and a domain that accepts everything is a dumping ground that defeats the purpose. |
| **Published language and semantic contracts** | Two components or products sharing data about the same entity; any breaking-change dispute; coupling decisions. | A domain publishes a canonical definition of each shared entity; consumers couple to declared semantic intent ("requires: customer_classification"), never to internals like column names. |
| **Architectural quantum** | Drawing deployment or ownership boundaries; deciding what "one unit" of a system is. | The smallest independently deployable unit with high functional cohesion, carrying everything its function needs: logic, contract, metadata, infrastructure declaration. |
| **The published gate — safe-by-construction at the right altitude** | Designing any validation; deciding WHERE a failure should surface; consumer-facing errors that trace to producer omissions. | Move validation to the altitude where the person who can fix it meets it: a product missing classification fails at the owner's publish step with an actionable message — never as a consumer's read-time 500. |
| **Fail-closed vs fail-open — choose the posture per concern** | Designing any failure path, fallback, degradation, or health check. | Degradation is designed, never discovered. |
| **Falsifiable success metrics** | Writing any goal, contract, exit criterion, or "definition of done". | "How will we know?" must answer with a command and an expected output — "when [command] returns [result]" — never with "looks good" or "feels right". |

## Seats (open registry — any model, runtime, or human)

| Seat | State | Promise |
|---|---|---|
| **orchestrator** | active | Owns decomposition and dispatch. Publishes intents and validation contracts, decomposes initiatives into promises, assigns seats. Never writes production code. |
| **builder** | active | Implements one contracted unit of work in an isolated worktree, self-checks against the contract, and submits evidence. The default production seat. |
| **reviewer** | active | Independent adversarial assessor. Judges a builder's promise against the ratified contract and repo conventions, from clean context. Its promise is honest assessment, not approval. |
| **validator** | active | Verifies the live effect against the contract on the deployed/running system — not the diff. Drives the real thing and records observed behavior as evidence. |
| **scout** | active | Bounded research on a specific question; returns a compact, decision-ready brief. Stores durable findings as reference memories. |
| **analyst** | active | Produces objective structural telemetry — dependency graphs, hotspots, coupling, coverage — measurements, not advice. |
| **adversary** | active | Competing-hypothesis investigation: multiple heads each champion a different theory and actively try to disprove the others. For debugging with unclear root cause. |
| **architect** | provisional | Non-coding engineering seat: produces ratified ADRs, runbooks, and documentation through the same contract/assessment loop builders use for code. |
| **librarian** | provisional | Agentic retrieval seat (evolution L3): promises decision-ready context — decomposes the question, walks the link graph, assesses freshness, returns a briefed bundle with provenance. |

Full seat envelopes: `.socom/canon/roles.xml` (compiled agents in `.claude/agents/`). Builder and reviewer never share context. Briefs open with the user's words verbatim.

## Gates

| Gate | Trigger | Tier | Band | Blocks |
|---|---|---|---|---|
| session-start | session open | fast | red | working on stale or drifted state |
| task-completion | marking work done | fast | red | the done transition |
| pre-commit | git commit | medium | amber | nothing locally (amber); the breach record feeds trust scoring |
| pre-push | git push | full | red | the push (bypassable locally; never in CI) |
| eval | measurement / on demand / pre-ship | fast | red | shipping on an unmeasured or below-threshold pass-rate |
| ci | push / pull request | ci | red | the merge |
| session-end | session close | medium | red | a vanishing session |

Local bypass is permitted for flow; CI re-asserts every gate. Run a gate: `socom gate <id>`.

## Forge — git-provider operations (universal verbs, repo-bound commands)

Run `socom forge <verb>` — NEVER improvise provider mechanics (auth, polling, MR calls) inline.

- **poll-yourself** — Long-running forge operations (CI runs, merge checks) are watched BY the agent — background loop or watcher — never framed back to the human as "should I keep monitoring?". The human hears outcomes.
- **cache-free-state** — State queries (ci-status, mr-status) must hit the provider's API directly. Provider CLIs that serve cached listings are bound through their cache-free forms; a stale answer is worse than a slow one.
- **verify-after-push** — A push is not done at exit 0: after every push, query ci-status and carry the result into the evidence. A push with a failing pipeline is not "done" (constitution §verify-never-claim).
- **auth-is-bound-not-improvised** — Credentials and token plumbing live in the binding (or the provider's credential helper), never improvised per-session. If auth fails, fix the binding — do not inline secrets into commands or files.

| Verb | Intent | This repo |
|---|---|---|
| `push` | Push the current branch to the canonical remote, with whatever auth the provider needs. | *unbound* |
| `ci-status` | Latest pipeline/workflow state for this repo — result, status, branch. Cache-free. | *unbound* |
| `ci-run` | Queue the repo's primary pipeline on a branch (extra args pass through). | *unbound* |
| `ci-watch` | Block-and-poll a run to a terminal state, emitting transitions; used by background watchers per rule poll-yourself. | *unbound* |
| `mr-open` | Open a merge/pull request from the current branch to the default branch (title from args). | *unbound* |
| `mr-status` | State of open MRs/PRs for this repo — id, title, vote/check state. Cache-free. | *unbound* |
| `repo-web` | Print the repo's web URL (for handoffs and humans). | *unbound* |

## Residuality — the falsifiable gate (constitution §residuality-gate)

Run before any fix or hard-to-reverse decision. A "yes" to any gate question is a STOP — rework or leash it.

- **relocate-not-remove** — Does this relocate stress rather than remove it? A fix that moves load, contention, or failure pressure to another component, layer, or future session has not removed the stress — it has hidden it where the next person meets it cold. Remove the stress at its source or name where it now lives.
- **hidden-assumption** — Does this hide a quantitative assumption? "Raise the limit", "add a buffer", "bigger node" all encode a number nobody wrote down. Surface the assumption (what value, why, when it breaks) or the fix is a silent time bomb.
- **symptom-not-class** — Does this patch the visible symptom instead of the class? If the same bug can recur one field, tenant, or path over, the class is still open (constitution §fix-the-class). Patch the instance to mitigate now; the objective remains the class-level fix, same session.
- **one-way-door** — Does this open a one-way door? A hard-to-reverse decision (schema, public contract, deletion, migration) must fail safe, not into disaster — Saltzer's core distinction. If reversing it is expensive or impossible, it earns a design-review and an explicit rollback story before it lands.
- **trigger-words** — These words demand the gate, every time: pin, bump, raise the limit, add a retry, add a buffer, bigger node, works for now, temporarily, good enough. Reaching for one is the signal that stress is being relocated, not removed.

Falsifiable checklist — Saltzer & Schroeder (1975) principles, each a test a design can be failed against:

- **economy-of-mechanism** — Keep the mechanism as small and simple as possible — what cannot be inspected cannot be trusted. SOCOM: lean canon, "port the pattern, not the code", §context-economy. Fail it when a change adds mechanism it cannot justify.
- **fail-safe-defaults** — Base decisions on permission, not exclusion: a design error should deny, not grant. SOCOM resolves the velocity tension by altitude — gates fail OPEN locally (warn, exit 0) but fail CLOSED in CI where the fixer meets them (the published-gate doctrine). Fail it when an error path grants instead of refusing.
- **complete-mediation** — Check every access to every object, including at init, recovery, shutdown, maintenance. SOCOM: gates at every band — session-start, task-completion, pre-commit, pre-push, ci, session-end. Fail it when a path skips the check.
- **open-design** — Security must not depend on secrecy of the mechanism. SOCOM: §git-is-source-of-truth, the open seat registry, the L0 grep floor — the whole substrate is inspectable. Fail it when correctness relies on something hidden or unwritten.
- **separation-of-privilege** — Require two keys, not one. SOCOM: builder and reviewer never share context; a worker cannot amend its own contract; assessment is never delegated to the promiser. Fail it when one actor can both act and bless the action.
- **least-privilege** — Every actor operates with the minimum privilege its function needs. SOCOM: domain-scoped claims with TTL auto-expiry, isolated worktrees, bounded seat promises. Fail it when a change grants more reach than the task requires.
- **least-common-mechanism** — Minimize mechanism shared across actors — shared state is a coupling and an information path. SOCOM: an isolated worktree per session, never the shared checkout. Fail it when a change forces unrelated work through one shared point.
- **psychological-acceptability** — Make the protected path the easy path, or people route around it. SOCOM: velocity-first — gates warn-not-block locally precisely so they are never disabled. Fail it when the safe path is so painful it invites bypass.
- **work-factor** — Weigh the cost of doing it right against the cost of going around. SOCOM inverts it: renegotiating a contract is deliberately CHEAPER than bypassing it. Fail it when the wrong path is the cheap path.
- **compromise-recording** — When you cannot prevent, record — a detectable breach beats a silent one. SOCOM: the breach ledger (`socom breach`), amber gates that warn-and-log and feed trust scoring. Fail it when a fail-open path leaves no trace.

## Repo bindings (socom.yaml)

| Check | Command |
|---|---|
| fast | `tests/smoke.sh` |
| medium | `tests/smoke.sh && python3 -c "import xml.etree.ElementTree as ET,glob; [ET.parse(f) for f in glob.glob('canon/*.xml')+glob.glob('schemas/*.xml')+glob.glob('.socom/canon/*.xml')]; print('xml well-formed')"` |
| full | `tests/smoke.sh && ./bin/socom index . >/dev/null && echo full-ok` |
| ci.status | `echo 'bind me: cache-free pipeline state query'` |

Domains: protocol, cli, canon

## Retrieval map

- Entering a phase? Load that section of `.socom/memory/INDEX.md` (session-start / mid-session / closeout / always-on).
- Working a domain? Load its file via `.socom/lessons/index.md`.
- Associative recall: `socom index` emits chunks for any vector store; the substrate never depends on it (L0 floor: this file + grep).
