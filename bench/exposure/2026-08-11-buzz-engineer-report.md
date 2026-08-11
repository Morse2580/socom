# Field report — engineer on `buzz` — 2026-08-11

> ⚠️ **THIS IS NOT A PROTOCOL RUN.** It is a written report received after the
> fact and relayed by the operator. `TEMPLATE.md` is an **observer's** sheet for
> a live or async *observed* session with a muted observer, an opening line said
> once, and a recruitment screen. None of that happened here. Recorded on the
> sheet shape so it is comparable, with every unobserved cell marked
> `NOT OBSERVED` rather than inferred.
>
> **What it therefore is:** the strongest field evidence on file, and weaker than
> a conforming run. Whether it counts toward [[EV-NONAUTHOR-EXPOSURE-01]] is an
> **operator ruling** — see `decisions/0008` and §6.
>
> Row: [[EV-NONAUTHOR-EXPOSURE-01]]. Protocol: [`README.md`](README.md).

## 1. Before the session

| | |
|---|---|
| Participant | An engineer, **not the author** — first non-author on file |
| How they were recruited | `NOT OBSERVED` — relayed by the operator; whether socom was suggested to them or they reached for it is **unknown and material** |
| **Do they owe me a favour?** | `NOT SCREENED` — the prohibition was not applied because this was not a recruited session |
| Drives AI agents on a real repo? | `NOT OBSERVED` |
| Platform | `NOT OBSERVED` — Rust toolchain in a local `bin/` requiring activation |
| Repo — theirs, real? | **`buzz`** — real, Rust, `Cargo.toml`, `justfile` (`just setup`/`check`/`ci`), has its own hooks |
| **Build under test** | `NOT RECORDED` — ⚠️ **no `socom version` digest.** A result that cannot name its build is not reproducible evidence (README). The digest is the one cell that cannot be reconstructed after the fact |
| Preflight clean? | Implied by "installed the tool and ran its one-command setup" — not separately reported |
| Mode | **Async written report, after the fact.** No observer present |

## 2. (a) STALL POINT

| t+ | What they were trying to do | What stopped them | Verbatim | Recovered? |
|---|---|---|---|---|
| — | Run the gate after one-command setup | `checks.fast` bound to `cargo test`; `cargo` not on PATH | *"When I ran the gate, it failed instantly with 'cargo: not found.'"* | **Yes — by hand, from outside the tool** |

**They recovered.** This is the material difference from
[`2026-08-07-akili.md`](2026-08-07-akili.md), where the participant escalated out
and did not recover inside the tool. Here they diagnosed it, rebound
`checks.*` to `just` targets, and continued.

**Their diagnosis, verbatim:** *"it checked whether a file existed, not whether
the command actually runs."*

**Their severity argument, verbatim:** *"If you'd walked away after setup, that
gate would have been red on every single commit, forever, for a reason that has
nothing to do with your code. And because the failure message just says 'checks
failed,' you'd think your tests were broken rather than that the tool never
worked."*

**Their charge against the tool's own promise, verbatim:** *"the guide makes a
specific promise: when it can't figure something out honestly, it tells you and
stops. It guessed and reported success."*
*(Verified in the repo: the promise is `verify-never-claim`,
`canon/constitution.xml:6`, **`rank="1"`** — socom's first principle.)*

## 3. (b) DID A BOUND GATE CATCH SOMETHING REAL

| | |
|---|---|
| Did a gate fire on real work? | **NO — and this is the rule, not a quibble** |
| What it caught | A formatting error **they planted deliberately** to test the gate. Caught with exact file, exact line, exact fix; reverted; green again |
| Was the defect pre-existing / organic? | **No — planted** |
| Did they fix it, or bypass it? | Reverted it |
| Did they agree it was worth catching? | `NOT OBSERVED` |

⚠️ **§3's own rule excludes this:** *"A defect the participant planted in order
to test the gate does **not** count — 3/5 of the agent cohort did exactly that
and it produced zero evidence of value."* A fourth party has now done the same
thing. **It proves the mechanism works end-to-end when correctly bound — the
first such proof by a non-author — and it is NOT evidence of value.** Do not let
the two be conflated; the sheet was written to stop exactly that.

## 4. Free findings

| Question | Observed |
|---|---|
| Reached for `--no-verify`? | `NOT OBSERVED` |
| A gate fired a FALSE POSITIVE | **YES — the whole finding.** `checks.fast` red on every commit for a reason unrelated to the code |
| A metric misled them | **YES, twice.** (a) `✓ … gates now run YOUR tests` over an unrunnable command. (b) *"93 chunks of knowledge retrievable"* — **all 93 are socom's own documentation; none of `buzz` is indexed** |
| Where discovery stalled | §2 |
| They "gamed" a gate | No |

**What they thought socom was FOR:** *"its main trick: figure out how to run your
tests, automatically, so its quality gate has something real to check."* Worth
noting — that is a narrower pitch than `VISION.md`'s, and it is the half that
broke.

**Did they hit the adoption surface and react to it?** **Yes, and favourably in
one respect:** socom wrote `CLAUDE.socom.md` rather than overwriting their
`CLAUDE.md`, and they called it out unprompted — *"which is the right call and it
got it right."* That is
[[DEF-QUICKSTART-REFUSES-TO-ADVANCE-ON-A-HAND-WRITTEN-CLAUDE-MD]]'s 2026-08-06
repair **confirmed in the field by a non-author**. They also flagged
`.gitignore` as the only edited file, inside marked boundaries — accurate, and
independently confirmed in socom's own checkout the same day.

## 5. (c) VOLUNTARY SECOND USE — the metric

**PENDING — not askable on the protocol's terms.** §5 requires a separate
sitting one week after a run, with the participant not reminded socom exists in
between. This report arrived unsolicited and the operator is in contact with
them. Whether a §5-equivalent can be asked here without contaminating it is an
**operator judgement**.

| | |
|---|---|
| Date asked | |
| **Ran a socom verb again, unprompted?** | **PENDING** |

⚠️ This is a **separate** metric from `2026-08-07-akili.md` §5, which asks
whether **the operator** returned and is due 2026-08-14. Neither substitutes for
the other.

## 6. Verdict

| | |
|---|---|
| Stall point recorded? | **Yes** — `checks.fast` → `cargo: not found`. **Third sighting of the class**, second in the field |
| Unstaged gate catch? | **No** — the catch was planted (§3) |
| **Voluntary second use?** | **PENDING** (§5) |
| Any prohibition broken? | **Not applicable — and that is the finding.** The prohibitions (`demo` · `favour` · `doc-fix-first` · `agent`) are screens applied when *recruiting*. None was applied, because nobody recruited. The run is not *void*; it is **unscreened**, which is a different and lesser defect |

**Proof tier after this report:** **operator to set.** Unchanged position from
`0006`: the `D0`/`D1` vocabulary lives in `/root/Akili/.claude/skills/root-gate`
and nothing in this repo defines it.

**What this report says the next action is:** rule on `decisions/0008` — whether
the third sighting of the detect-then-claim class lifts that row's P1 hold. See
§7.

## 7. Rows this report generated

| Finding | Disposition |
|---|---|
| `_detect_checks` picks a command from **file existence** and `quickstart` prints `✓ … gates now run YOUR tests` without resolving it. *(Verified: `install.py:255` is `(root / "Cargo.toml").exists()`; `install.py:364` is the print; `shutil.which` exists in this codebase and is applied correctly at `spawn.py:413` and `install.py:331` — the guard is inconsistently applied, not missing.)* | Appended to [[DEF-STATUS-CLAIMS-UNLABELLED-01]] as the **third sighting** — not a new row, same class. **The P1 hold is now contested: see `decisions/0008`** |
| `socom index` reports *"93 chunks"* of the **tool's own** documentation and cannot reach the adopted repo's code. *(Verified: `cmd_index`, `retrieval.py:75`, globs `(root / SOCOM_DIR).rglob("*.xml")` — `.socom/` only.)* | **NEW — needs a row.** Same class as `DEF-STATUS-CLAIMS-UNLABELLED-01` (a true number that implies something false), but a distinct surface with a distinct fix. Not filed by this sheet |
| socom took `core.hooksPath` because `buzz`'s hooks were **uninstalled** (`just setup` never run in that clone), so `.git/hooks/` was genuinely empty. `_default_hooks_present` (`lifecycle.py:426`) behaved **correctly**. The uncovered risk is the **later collision**: install the repo's hooks afterwards and git silently ignores them, with no warning. | **NEW — needs a row.** Narrower than reported: not a detection failure, a no-warning-on-later-collision failure |
| `CLAUDE.socom.md` sidecar confirmed in the field by a non-author | **Evidence, not a defect.** Cross-referenced above |
| Binding `checks.full` to `just ci` makes the next push run full CI on a cold cache | **Not a socom defect** — a consequence of the participant's own binding choice. Recorded so it is not mistaken for one |
