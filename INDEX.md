# SOCOM — Program index

> **What this is:** an inventory of socom's own surface against the runtime state
> it has actually produced, and a leverage ranking derived from the gap.
> **Measured 2026-08-10 at `083e844`.** Every figure below has a probe next to it;
> re-run rather than carry — the numbers move on any merge.
>
> **What this is NOT:** a queue. Everything in `buckets/build.md` reads BLOCKED,
> `0002` is HELD at the gate, and every P1 is deliberately unrepaired. This
> document ranks leverage so the ordering is ready when
> [[EV-NONAUTHOR-EXPOSURE-01]] §5 is filled. It authorises nothing.
>
> **Why it exists:** the operator's read was *"so much that is not actually doing
> [anything], and so much not aligned, that it gives the feeling of no path
> forward."* The feeling is accurate. The cause is not drift. §4 names it.

---

## 1. Scale

| Thing | Count | Probe |
|---|---|---|
| Verbs | **40** | `COMMANDS` dict, `src/socom/cli.py:32-49` |
| `src/socom/` | **7,378** lines | `wc -l src/socom/*.py` |
| …of which `cmd_*` handlers | **2,524** lines | per-verb AST-ish slice, see §2 |
| Canon | **786** lines / 8 files | `wc -l canon/*.xml` |
| Root docs | **~1,989** lines | `README PROTOCOL PILOT ROADMAP VISION GAPS RESIDUALITY* STORAGE` |
| Decisions | **7** | `ls decisions/` |
| **Runtime state in this checkout** | **5 files** | `find .socom -type f` |

Those five files: two handoffs (last `H-2026-08-06-main.xml`), one next-session
prompt, a 12-chunk index, one lease shard.

## 2. The surface, by layer

| Layer | Verbs | Handler SLOC | Runtime state ever produced |
|---|---:|---:|---|
| **Substrate ops** — `init` `compile` `doctor` `gate` `index` `handoff` `prompt` `install` `quickstart` `uninstall` `version` `adopt` `unadopt` `greet` `statusline` `hydrate` `mcp` `breach` `context` | 19 | 1,272 | **LIVE** — run every session and in CI |
| **Blackboard** — `claim` `release` `attest` `findings` `resolve` | 5 | 140 | **2 rows, ever** (§3) |
| **Measurement** — `cycle` `judge` `eval` `contract` `lesson` `introspect` `value` `baseline` `embed` `query` | 10 | 750 | **None** |
| **Orchestration** — `monarch` `spawn` `trace` `meter` `precond` `forge` | 6 | 362 | **None** |

Module investment tells it more plainly: `blackboard.py` is **911** lines,
`monarch.py` **866**, `spawn.py` **468**, `retrieval.py` **702**. That is ~2,900
lines — **39% of `src/`** — behind the three layers that have produced almost
nothing.

**Four verbs are invoked by no test at all:** `judge`, `meter`, `statusline`,
`trace` *(probe: grep for invocation, not mention, across `tests/`)*.

## 3. The three measurements that explain the feeling

**a. The blackboard has never carried a finding.** `refs/socom/blackboard`
exists on `origin` at `cdc14d4`. Its entire contents, across its whole life:

```
{"kind": "lease",   "paths": ["--help"], "ts": "2026-08-06T06:38:52+00:00", ...}
{"kind": "release", "ref": "l-5dd8f7a55296", "ts": "2026-08-06T06:39:19+00:00"}
```

One lease and its release, on the path `"--help"` — which is not a path. It is
the residue of the flag-parsing bug documented at `src/socom/cli.py:54`.
**Zero `attest`, zero `findings`, zero `resolve`.** The differentiator no harness
in the 2026 literature has (see `0007`) has never carried a real finding.

**b. The eval gate is RED and has never had anything to score.**

```
$ ./bin/socom gate eval
socom cycle: no ledger — .socom/ledger/runs.jsonl absent. Nothing measured yet;
append runs before rolling a cycle (R6: degrade loudly, never a silent empty cycle).
socom gate eval: RED — checks.eval failed (rc=1)
```

`.socom/ledger/` does not exist. This is R6 working exactly as designed *and*
the sharpest available statement of the problem.

**c. socom's own `ci` gate is bound to a placeholder.** `canon/gates.xml` calls
`ci` "the incorruptible floor (R1)"; `socom.yaml` binds it to
`echo 'bind me: cache-free pipeline state query'`.

## 4. The diagnosis — build order, not misalignment

Every empty layer is **second-order**: it measures or coordinates work that
someone else does. socom has never had a workload flowing through it. One user,
working on socom itself, and `.gitignore:7` excludes `/.socom/` deliberately
(`546227e` — *"ship the tool, not a self-adoption"*). **The substrate has no
substrate to sit under.**

So ~39% of the code was built ahead of the evidence that would say which parts
matter. `0001` — exposure before capability — already named this, and was
ratified *after* most of that layer existed. Nothing here is drifting from a
plan; the plan arrived late and the earlier build has not been re-litigated.

That is also why the queue is one question. It is not an empty queue by
accident. It is the correct queue for a repo whose remaining decisions are all
downstream of a measurement in flight.

---

## 5. Leverage ranking

Axis: **evidence produced per unit of effort**, given that the binding
constraint is *no workload has ever flowed through socom*. Not "value if it
worked" — leverage on the thing actually blocking.

### 1 — Fill §5 on 2026-08-14. `EFFORT: one question.`
Highest by an order of magnitude, already scheduled, costs nothing. It is the
only act that produces evidence about whether anyone returns to the tool, and
every other item is downstream of it. §3 raises its stakes: §5 is no longer just
whether one row closes, it is the first datum on whether **anything** flows
through the substrate at all.
⚠️ Do not fill early and do not prompt it — see the sheet and `0001`.

### 2 — Let socom self-adopt LOCALLY, without committing it. `EFFORT: ~1h. NOT AUTHORISED.`
The reversal at `546227e` was about not **committing** socom-in-socom, and
`.gitignore:7` already excludes `/.socom/`. Running `socom adopt` in this
checkout and leaving the state untracked does not reproduce what that commit
reversed. It is the only path by which the Measurement layer — 10 verbs, 750
handler SLOC, `retrieval.py`'s 702 — ever receives a single real row, and it
turns `gate eval` from a structural RED into a number. **25% of the verb surface
is currently unfalsifiable**, and this is the cheapest thing that changes that.
*Flagged as a decision to revisit, not a bug: the reversal was deliberate and
its reasoning has not been re-read against this distinction.*

### 3 — Typed gate result (`0007` item 1). `EFFORT: medium. BLOCKED on §5.`
`run_check` (`src/socom/gate.py`) returns a bare `returncode`; output is
inherited and never captured. Replacing it with
`findings[]/metrics[]/guidance[]/score/success/summary` makes **a gate finding
become a blackboard finding** — which converts §3a from a dead differentiator
into a live one as a *byproduct of gates people already run*, asking nobody to
adopt a new habit. No dependency; `attest` already owns the store. Ranked below
#2 because it needs a workload to be worth anything, and #2 is what creates one.

### 4 — `guidance[]` wiring (`0007` item 2). `EFFORT: low. BLOCKED on §5.`
The rationale content already exists — 786 lines of canon with `embed="true"`
descriptions, written for agent consumption — and is simply never attached to a
red band. Wiring, not authorship. Rides on #3.

### 5 — Retire or quarantine the Orchestration layer. `EFFORT: low. NOT AUTHORISED.`
`monarch.py` + `spawn.py` = **1,334 lines**, zero runtime state, and `meter` and
`trace` are invoked by no test. This is the highest-leverage *subtractive* move
and the direct answer to *"so much that is not actually doing anything"* —
deleting surface is cheaper than validating it. Ranked fifth, not first, because
`0001` blocks it as surely as it blocks building: **removing capability before
the exposure evidence is in is the same unjustified act as adding it**, and
`spawn --exec` is cited as MEASURED evidence in `0002` claim 8.

### 6 — Bounded attempt budget (`0007` item 3). `EFFORT: low. BLOCKED on §5.`
Real gap — socom caps seconds (`limits.max_runtime_s`) and caps blocking
(amber/red) but never attempts. Ranked last because nothing is currently
retrying anything.

### Not ranked — refused, see `0007`
Sidecar daemon; vendoring concrete sensors; the devbox; MCP tool sprawl.
**And `DEF-STATUS-CLAIMS-UNLABELLED-01` stays READY P1 past §5** — repairing it
deletes the finding `PILOT.md` collects (`0001` §Amendment 1 rule 3).

---

## 6. What this index does not claim

- **It is not evidence about socom's value.** An unused verb is not a bad verb;
  it is an unmeasured one. The distinction is `0004` Class A applied to socom's
  own inventory, and this document is subject to it.
- **It does not amend `0001`.** If anything it strengthens the ratified ordering:
  an empty measurement layer is the best argument on file that capability built
  ahead of exposure does not get used. That cuts *against* the enforcement-first
  amendment `0007` flags from the external sources. Both belong to the operator.
- **It sets no proof tier** and flips no bucket row.
- **It authorises nothing.** Items 2–6 are capability or its inverse. §5 first.

**Probes:** `find .socom -type f` · `git ls-remote origin 'refs/socom/*'` ·
`git show refs/socom/blackboard-remote:leases/*.jsonl` · `./bin/socom gate eval` ·
`wc -l src/socom/*.py canon/*.xml` · `grep -c '"' src/socom/cli.py` (COMMANDS)
