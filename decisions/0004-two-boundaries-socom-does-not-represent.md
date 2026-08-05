# 0004 — Two boundaries socom does not represent

**Status:** Accepted 2026-08-05 — **diagnosis only; adopts no code and repairs nothing.**
**Supersedes:** nothing. **Subsumes:** the class named in
[`0002`](0002-unresolvable-enforcement-must-record.md), which is the intersection
of the two named here.
**Resolves:** what class the 2026-08-05 field findings belong to, and which of
them — if any — may be repaired before `EV-NONAUTHOR-EXPOSURE-01`.
**Does not touch:** the exposure, which remains the blocking row and is still unrun.

---

## Context

On 2026-08-05 socom was run against three real repositories on two machines by
the operator: `httpie/cli` (third-party, shallow clone), `cargo-applications`
(operator's own project), and `Morse2580/monarch-hris-platform` (operator's own,
Poetry/pytest). Build `1bc70ac4f16c` throughout — the public artifact, byte-identical
to `bin/socom`, verified by `cmp` and by digest reproduction.

Eleven distinct findings came out of it, on top of the three P0s repaired that
morning and the 5-substrate agent sweep the day before. This document exists
because rank 4 of the constitution requires it: *"Every initiative's objective is
to make an entire class of problem structurally impossible at the root — never to
patch the visible symptom."* Three P0s were patched that morning as three
instances. This is the class they were instances of.

**Every code reference below was re-grepped against the tree at `7b73efd`, not
carried from the rows that first recorded them.**

---

## Class A — socom reports what it WROTE, not what took EFFECT

Every claim in the table is derived from the act of writing a file or a config
line. None of them observes a result. The surfaces are independent, the shape is
identical.

| Surface | Derived from | Effect it asserts | Ref (VERIFIED) |
|---|---|---|---|
| `T6 — operational (L1 retrieval live)` | `vectors.json` **exists** | L1 beat the recorded floor | `lifecycle.py:941`; T5's own message at `:942-944` states *"L1 must beat the recorded floor before it serves"*, and `eval.json` — which carries a real `passed` boolean — is **written and never read** (`retrieval.py:313` is the only occurrence) |
| `✓ bound checks.fast/medium/full → 'pytest -q' — gates now run YOUR tests` | a line socom just wrote to `socom.yaml` | the command runs | `install.py:284` — **rc=127 on 3 of 3 repos measured** |
| `gate catches N … slips stopped before they landed` | line count of `breaches.log` | slips were stopped | `value.py:128` — every `log_breach` call site is an AMBER path that **proceeds**; RED is a bare `sys.exit` recording nothing |
| `socom gate <x>: checks.<t> unbound — passing` | absence of a binding | the gate passed | `gate.py:297` |
| `33%` / `100%` adoption, rung `T2`/`T6` | files socom planted | adoption | `lifecycle.py:922-947` (`adoption_rung`) — every rung tests a **file's existence** |
| `.claude/settings.json: kept your statusLine` | a `settings.json` socom wrote ~30 s earlier in the same command | deference to the user's config | `lifecycle.py:362` — **MEASURED: the file is untracked in `monarch-hris-platform`; `git show HEAD:.claude/settings.json` → `exists on disk, but not in 'HEAD'`** |
| `✓ .gitignore: socom runtime state ignored — `git add -A` is safe` | socom's own ignore block | safety | printed in a directory where `git add` cannot run at all |
| `socom release: no live lease held by this session` | its own derived identity | the board holds nothing of ours | fixed 2026-08-05 (`2fd2b5d`); it trusted an in-memory author over the published record |
| `claim: acquired …` on an unreachable remote | the local append succeeding | the lease is visible to peers | [[DEF-BLACKBOARD-GRANTS-ON-UNREACHABLE-REMOTE-01]], open |

### The self-indictment

Rank **1** of socom's own constitution, `verify-never-claim`:

> No task is done until concrete proof is shown. *"It should work"* is a
> violation: run the check, paste the output. Evidence from a different session,
> or from before the final change, does not count.

`quickstart` prints that sentence. It is result #4 of the demo query, in the
`[try it]` block, in **every** transcript captured on 2026-08-05 — including the
run that asserted `gates now run YOUR tests` about a command that did not exist
on the machine printing it.

**The tool built to stop agents from claiming without proof is the participant
most systematically in violation of its own rank-1 rule.** Class A is not a
collection of wording bugs. It is socom exempting itself from its constitution.

---

## Class B — socom writes what it does NOT OWN, and no code represents "own"

| Target | Whose | What happened | Status |
|---|---|---|---|
| `core.hooksPath` | host's | hijacked, unrecoverably | fixed — prior value recorded (`lifecycle.py:390`) |
| the git remote | host's | `claim` pushed `refs/socom/blackboard` to it, unasked | fixed — opt-in (`blackboard.py:341`) |
| the exit from adoption | host's decision | any later heal silently reversed it | fixed — exit recorded (`lifecycle.py:401`) |
| the working directory | host's | 33 files planted into a non-git scratch dir; readout `33% · T2` | **open** — [[DEF-QUICKSTART-REPORTS-ADOPTION-IN-NON-GIT-REPO-01]] |
| `.claude/settings.json` | host's | `statusLine` rewritten on first pass, then reported as "kept yours" | **open** |
| where the binary lives | host's | landed inside the adopted repo, unignored, with the PATH symlink resolving into it | **open** — [[DEF-INSTALLED-BINARY-LANDS-INSIDE-THE-ADOPTED-REPO-01]] |
| `.gitlab-ci.yml` | host's | **REFUSED** — *"exists and is not socom-generated"* | correct |

### The contrast case is the proof

`core.py:141` is the **one place in 6,958 lines where ownership is explicitly
represented in code** — a test for whether a file is socom-generated before
writing it. It is also the one row in that table where socom behaved correctly.

And on 2026-08-05 the operator read that refusal as the one thing that had gone
wrong in the install. It is the opposite: it is the only place the safety claim
in `PILOT.md` is mechanically enforced rather than asserted. A guarantee being
kept, printed in the register of a failure.

**`repo_root()` (`core.py:81`) is where Class B originates for the directory
case:** it walks up from cwd for `.git` or `socom.yaml` and, finding neither,
**returns cwd**. Failing soft is correct for `doctor`, which only reads. For a
command that writes 33 files into someone's filesystem it is the wrong default,
and it creates a second-order trap — once `socom.yaml` exists in a scratch root,
every later socom command run from any unmarked subdirectory resolves to it.

---

## The intersection is 0002

`0002` names *"enforcement whose declaration is durable, whose capability
resolves through a referent socom does not own, and whose resolution failure
degrades open without a trace."*

That is **A applied to B**: enforcement whose *effect* is unverified (A), on a
referent socom does not *own* (B). It is a subset — which is exactly why it did
not cover the metric findings, and why sweeping it found six instances rather
than the eleven now on file. `0002` stays HELD; nothing here unblocks it.

---

## What the morning's three repairs prove about the class

The three P0s fixed on 2026-08-05 (`2fd2b5d`) each ended in a mechanism that
records a host-owned write and makes it reversible:

| Repair | Mechanism | Line |
|---|---|---|
| hooks hijack | `socom.priorhookspath` | `lifecycle.py:390` |
| unadopt reversed | `socom.unadopted` | `lifecycle.py:401` |
| claim pushed to host origin | `blackboard.sync` opt-in | `blackboard.py:341` |

**Three separate ad-hoc implementations of one missing concept, sharing not a
line of code.** Each was a correct instance repair and each is defensible on its
own; together they are the diagnosis. By rank 4 — *fix the class, not the
instance* — that morning patched three symptoms and left the class standing.
Recorded here rather than filed as three green checkmarks, because a repair that
does not know it is one of a family is how a family grows.

---

## The operative question: repair before the exposure, or not?

The field evidence is strong enough that "shouldn't we fix this before showing
anyone" is now the obvious reaction. It is also the reaction `0001` was written
to survive: five months, six artifacts, zero non-author users, proof tier **D0**,
and every repair to date — including the three that morning — moved it by nothing.

**The test is not severity. It is: does the defect CORRUPT the measurement, or
PRODUCE it?** That test is already `0001` §Amendment 1 rules 2 and 3. What was
missing until today was evidence to sort by it.

| Finding | Corrupts / Produces / Neither | Disposition |
|---|---|---|
| Adopting a non-git directory by accident | **CORRUPTS** — the participant spends the whole session measuring a scratch folder; the result informs nothing | mitigate, see below |
| `100% · T6` decoupled from capability | **PRODUCES** — `PILOT.md` asks *"did a metric mislead you?"* | hold (rule 3) |
| `gates now run YOUR tests`, unexecuted | **PRODUCES** — same question, sharpest instance | hold (rule 3) |
| `doctor: clean` while `gate fast` is RED | **PRODUCES** | hold (rule 3) |
| `kept your statusLine` (self-reference) | **PRODUCES** | hold (rule 3) |
| `REFUSED …gitlab-ci.yml` reading as an error | **PRODUCES** — §4 of the sheet captures exactly this reaction | hold (rule 3) |
| Binary lands in the repo; symlink into it | **NEITHER** — untidy, recoverable, no effect on the measurement | P1 |
| Blackboard grants on an unreachable remote | **NEITHER at n=1** — needs 2+ concurrent sessions | P1; blocks Phase 3a, not this |
| Unresolvable gate leaves no trace | **NEITHER at n=1** — needs days | P1 |
| CI adapter names a gate it never invokes | **NEITHER at n=1** — needs a push and a CI run | P1 |

**Exactly one finding corrupts the measurement, and it does not need a code
change to stop corrupting it.** The observer is present. The mitigation is one
line of protocol — confirm the participant is at a repository root before they
run anything — which costs nothing, ships nothing, and deletes no finding. A code
repair here would be the more expensive option *and* the one that risks touching
the metric surfaces the exposure is meant to test.

---

## Decision

1. **Both classes are named and recorded. Neither is repaired.** Both are
   root-level and structural, therefore capability under `0001`, therefore
   BLOCKED until `EV-NONAUTHOR-EXPOSURE-01` has run.
2. **The single measurement-corrupting instance is mitigated in the PROTOCOL, not
   the code:** `bench/exposure/README.md` gains a pre-session step — confirm
   `git rev-parse --show-toplevel` prints the repo the participant means to adopt.
   Zero code, zero deleted findings.
3. **`DEF-QUICKSTART-REPORTS-ADOPTION-IN-NON-GIT-REPO-01` stays P1**, with its
   severity note corrected (done, `7b73efd`) and the split recorded: the
   *refuse-to-plant* half is a Class B repair, the *what the percentage means*
   half is a Class A repair, and they are not the same work.
4. **Repair order after the exposure is set by what the participant reports, not
   by this document.** Writing the order now would be the same error as fixing
   the tool now: choosing from taste in the absence of the one measurement that
   was authorised.

### The structural forms, for when they are unblocked

- **Class A:** no surface may state a capability it has not executed. Derive the
  claim from an execution record (a command and its exit code), or state presence
  explicitly — *"present"* is not *"working."* One `command -v` at bind time would
  have caught all three repos measured today.
- **Class B:** every write target is typed `socom's` or `host's`. A host-owned
  write requires prior value recorded, a reversal path, and disclosure at the
  moment of writing — **one** mechanism, not the three now in the tree. `core.py:141`
  is the existing precedent and the place to generalise from.

---

## Trigger that reopens this

The exposure running. Whatever the participant stops on selects which class is
repaired first and how far. If the participant stops on something in **neither**
column, this document was wrong about the sort and should be amended before any
repair is scheduled.

---

## Provenance

Three repositories, two machines, one build, one day. `httpie/cli` @ `5b604c3`
(third-party) · `cargo-applications` (operator) · `monarch-hris-platform`
(operator, Poetry/pytest). Build `1bc70ac4f16c`, public artifact, `cmp`-identical
to `bin/socom`, digest reproduced by `shasum -a 256`. Every code reference
re-grepped at `7b73efd`. The `kept your statusLine` self-reference and the
`vectors.json`/`eval.json` gap were measured directly, not inferred from the rows
that first reported them.

---

## Appendix — proposed repairs, for when they are unblocked

⚠️ **This is design, not a plan.** Nothing here is scheduled. Decision §4 stands:
the repair order is set by what the participant stops on, not by this document.
An appendix that reads as a backlog is how a diagnosis turns into a build lane
under another name — which is the failure `0001` §Amendment 1 exists to prevent.

### Neither class needs new machinery

Both fixes are already implemented in this tree, for other purposes. socom does
not lack the primitives; it does not point them at itself. VERIFIED at `f97a6e2`:

| Primitive already in the tree | Used for | **Not** used for |
|---|---|---|
| `shutil.which` (`install.py:251`, `spawn.py:413`, `lifecycle.py:781`) | checking a **runtime** binary resolves | the check binding asserted at **`install.py:284` — 33 lines below, same file, same import** |
| `.socom/assertions/log.jsonl` — append-only `(command, exit)` rows (`lesson.py:350-399`) | `introspect`, over a handoff's `<evidence>` | any claim socom makes about **itself** |
| `write_generated`'s ownership test (`core.py:135-147`, HR2) | files — *"never clobber a file we didn't generate"* | git config, remotes, directories, the binary's own location |

That `shutil.which` sits 33 lines above the false claim it would have refuted, in
the same file, under the same import, is the tightest statement of Class A
available: the tool had the probe, used it for the thing it does not claim about,
and asserted the thing it does.

### Class A — every fix has two versions, in two different lanes

`DEF-STATUS-CLAIMS-UNLABELLED-01` scopes itself to **labelling only** and routes
"changing what a claim derives from" to [[SUBSTRATE-STATUS-TIER-SWEEP-01]],
BLOCKED. So each surface has a cheap version that makes the sentence honest, and
a real version that makes the underlying claim true. They are not alternatives —
the first is a stopgap the second retires.

| Surface | **Honest today** — labelling, in-bucket | **True tomorrow** — derivation, capability |
|---|---|---|
| `install.py:284` bind | `✓ bound → 'pytest -q' (bound, not verified — run 'socom gate fast')` | `shutil.which` the binary; print `verified on PATH` or `will fail: pytest not found` |
| `lifecycle.py:941` T6 | `T6 — L1 index present (not evaluated)` | read `eval.json`'s `passed`; hold at T5 if `eval` never ran |
| `value.py:128` catches | `N amber breaches logged (all proceeded)` | record RED blocks as well, after which *"stopped"* is true |
| `lifecycle.py:922` rung | print `enforcing: nothing` beside the percentage | each rung tests a capability, not a file's existence |
| `lifecycle.py:362` statusLine | `left socom's statusLine in place` | track the prior value; say *"kept yours"* only when it was yours |
| `gate.py:297` unbound | already honest in itself — the **rung** ignores it | an unbound gate contributes 0 to the rung |

**The class fix, distinct from all six instance fixes:** one
`assert_capability(surface, evidence)` helper that refuses to render a capability
word — `live`, `operational`, `runs`, `wired`, `safe`, `stopped` — without an
`(command, exit)` record, writing through the assertion log that already exists;
plus a test asserting no capability verb is printed outside it. **Only this one
stops the class regrowing**, and only this one makes rank 1 bind socom the way it
binds every other participant. The six rows above are instance repairs and should
be recognised as such — see §What the morning's three repairs prove.

### Class B — one mechanism replacing three

```
host_write(root, target, kind, apply_fn):
    1. is this ours or theirs?   generalise core.py:141 beyond files
    2. record the prior value    socom.restore.<key> — ONE namespace
    3. announce at write time    "socom is setting <target>; `unadopt` reverses it"
    4. register the reversal     unadopt walks the record; no per-case branches
```

This collapses `socom.priorhookspath` (`lifecycle.py:390`), `socom.unadopted`
(`lifecycle.py:401`) and the `blackboard.sync` opt-in (`blackboard.py:341`) into
one concept. Without it, `.claude/settings.json` and the binary's location become
the fourth and fifth ad-hoc keys, each correct in isolation and each proving the
class again.

**The split that ends the measurement corruption:** `repo_root()` (`core.py:81`)
fails soft and returns cwd. That is right for readers and wrong for a command
that writes 33 files. Writers take `repo_root_strict()`, which refuses in a
directory that is neither a git repo nor an existing socom root, and names the
path it was about to plant into. Every writing command prints its target root on
its **first** line — `repo:` currently appears on line 3, inside the logo block,
which is why a wrong-directory adopt read as a normal one.

### Cost

⚠️ **HYPOTHESIS — estimated, not measured.** No spike has been run on any of it.

| Work | Estimate | Lane |
|---|---|---|
| Class A, labelling column (6 surfaces) | ~2 h | repair — in `DEF-STATUS-CLAIMS-UNLABELLED-01`'s stated scope |
| Class A, derivation column | ~0.5 d | capability — `SUBSTRATE-STATUS-TIER-SWEEP-01`, BLOCKED |
| `assert_capability` + its test | ~1 d | capability, BLOCKED |
| `host_write` + `unadopt` rewrite | ~1–2 d | capability, BLOCKED |
| `repo_root_strict` + target-root on line 1 | ~2 h | borderline; a new refusal path, so treat as capability |

### Why even the two-hour column is held

The labelling column is cheap, in-bucket, and still **not** repaired before the
exposure — because five of its six surfaces are exactly what `PILOT.md` asks the
participant about (*"did a metric mislead you?"*). Cheapness is not the test.
Whether a repair **deletes a finding** is the test, and this column deletes five.
The only pre-exposure action remains the protocol line in Decision §2.
