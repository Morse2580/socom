<!--
CLAIM-VERIFY PASS — history. Every pass re-ran its claims; none were carried.
Passes 1-11 (2026-08-05 → 2026-08-08) are compacted to their standing verdicts:
  the byte count and build digest move on ANY merge touching `bin/socom` and
  must be re-measured every pass (Regression Test 1, hit three times);
  every `file.py:N` in this prompt is stale by the next edit — re-`sed` it, the
  SYMBOL is the durable cite (Regression Test 3);
  nine P0 repairs across eleven passes moved the proof tier by NOTHING;
  pass ELEVEN refuted the premise of the ten before it — the prompt said the
  exposure was UNRUN; it had run on 2026-08-07, three commits earlier. Probe the
  premise, not only the numbers.
Full pass-by-pass history: `git log -p prompts/next-session-run-n1-exposure.md`.

Pass TWELVE (2026-08-10, `569f4d2`) is compacted: it corrected `decisions` 6→7,
HEAD/CI, and the unnamed `INDEX.md`, and it caught six annotations reading
`@ f1dce80` on claims re-probed that day — the values matched, the measurement
point did not, which is the fail-closed rule's "the annotation lied" case.

REWRITTEN 2026-08-11 (THIRTEENTH pass). **This pass changes the SHAPE of the
file, not only its numbers.** A second field report arrived — from an engineer,
**not the author** — and the premise "the queue is one question" no longer holds
alone: a ruling is now pending. Everything below re-run today, not carried.
  REWRITTEN THE PREMISE ..... **A SECOND EXPOSURE EVENT IS ON FILE**, and it is
            the first by a **non-author**:
            `bench/exposure/2026-08-11-buzz-engineer-report.md` *(measured:
            `ls bench/exposure/` = README + TEMPLATE + **two** dated sheets)*.
            ⚠️ It is recorded as a **FIELD REPORT, not a protocol run** — no
            observer, no recruitment screen, and **no `socom version` digest**,
            which is the one cell that cannot be reconstructed later.
  REWRITTEN decisions ....... 7 -> **8 files**. `0008` added, **Accepted the
            same day by operator ruling, and REPAIRED** *(measured:
            `ls decisions/` = 8; `sed -n '3p' decisions/0008-*.md` reads
            "**Accepted 2026-08-11** — operator ruling")*
  REWRITTEN the P1 hold ..... `DEF-STATUS-CLAIMS-UNLABELLED-01` gained a
            **FOURTH sighting** (first by a non-author) and **surface 1 of 7 was
            REPAIRED** under `0008`. Row is **STILL READY P1** — six surfaces
            remain held under `0001` rule 3 *(measured: the row still reads
            `**READY P1**`; re-`grep` it)*. ⚠️ Do not finish the row.
  VERIFIED  §5 ............... `2026-08-07-akili.md` §5 still **PENDING**, still
            due **2026-08-14** *(L99 + L120)*. The new report does **not**
            substitute for it — §5 asks whether the OPERATOR returned; the
            engineer is a different person, with a separate and also-pending §5.
  REWRITTEN public artifact . 434361 -> 436923 -> **437237** bytes, `a1354b03b292` ->
            **`ad0cac783b19`** (two repairs shipped 2026-08-11), http=200, `cmp` byte-identical *(measured:
            `curl -w` + `cmp` + `version` after the 0008 repair shipped)*.
            **MOVED** — `bin/socom` changed. Regression Test 1, sixth time.
  REWRITTEN defects ......... 8 -> **10 READY P1** *(measured: 9/0/1/10 via
            `grep -cE`)* — two rows filed from the field report. P0 unchanged.
  VERIFIED  build.md ........ 1 READY (R1) + 8 BLOCKED, unchanged *(measured: 1/8)*
  VERIFIED  EV row .......... `EV-NONAUTHOR-EXPOSURE-01` still **READY P0** —
            correctly, because §5 is unfilled *(L15 @ `d85381b`)*
  REWRITTEN suites .......... unit 386 -> **399** / r1corpus 146 / gate full
            **PASS** / `build.py --check` clean *(measured: all four re-run
            after the `0008` repair)* — +9 from the `_resolve_check` assertions
  VERIFIED  code cites ...... all eight re-`sed`-ed, all resolve to the cited
            symbol, none moved *(mechanism verified: `bb_do_claim`
            `blackboard.py:520`, `is_generated` `core.py:137`, `log_breach`
            `core.py:94`, `_is_socom_binary` `install.py:41`, `_is_dev_checkout`
            `install.py:48`, `cmd_install` `install.py:80`,
            `compromise-recording` `canon/residuality.xml:95`,
            `BUILD-ACP-RUNTIME-SEAM-01` `buckets/build.md:73`)*
  VERIFIED  skills ........... four, unchanged *(verified `d85381b`:
            `git ls-files .claude/skills/`)*
  VERIFIED  proof tier ...... **operator to set** — `0006` §"does not claim"
            explicitly declines to derive it, and the `D0`/`D1` vocabulary is
            not defined in this repo. This prompt does NOT assert a tier.
  HYPOTHESIS none.

  ⚠️ **`0007` and `INDEX.md` are still NOT a queue.** Both are analysis. `0007`
  is Proposed — BLOCKED on §5; `INDEX.md` §6 authorises nothing, and its item 2
  was run, refuted and **withdrawn by operator ruling** on 2026-08-11.
  ⚠️ **`0008` WAS different, and it is now CLOSED.** Accepted by operator ruling
  and repaired the same day at `55d1397`. It was the one item in this repo that
  could move from analysis to work, and it did. **It is not a precedent a session
  may extend to itself** — `0008` §"counter-argument, kept" says so, and its
  §Acceptance records the operator's words and the reading taken, so a later
  session can overturn the reading rather than inherit it silently.

  ⚠️ NEW LABEL, declared so it is not read as an unlabelled claim. This pass
  uses a fourth annotation the `prompt-verify-pass` skill does not define:
    (not re-probed — <why, and where the verdict lives>)
  It covers claims verified in a PRIOR pass against a source OUTSIDE this repo,
  which no probe in this tree can re-run today: RFC contents, another repo's
  `CLAUDE.md`, and output measured on a build that has since shipped over.
  Folding them into HYPOTHESIS would understate a primary-source verdict;
  leaving them bare would fail the gate. Six lines carry it. Each names where
  the verdict lives so the next session can re-probe at the source if it needs
  to lean on one. If this convention survives a pass, promote it into the skill.
-->

# Next session — file two rows. §5 on 2026-08-14. `0008` is DONE.

> ⚠️ **The filename is historical.** It says "run-n1-exposure"; the run happened
> on 2026-08-07. The name is kept because thirteen verify passes of audit trail
> live in this file's history and `prompt-verify-pass` globs
> `prompts/next-session-*.md`. Same convention `0006` used for the row ID.

**Row:** `EV-NONAUTHOR-EXPOSURE-01` (`buckets/evidence.md`), **READY P0**, `n=1`
*(L15 @ `d85381b`)*.
**Governed by** `decisions/0001`, **amended by `0006`**.
**Sheet:** `bench/exposure/2026-08-07-akili.md` — §1-§4, §6, §7 are FILLED.
**§5 is PENDING and §5 is the metric.**

## What actually happened, and why this prompt changed shape

The exposure ran on **2026-08-07** under operator ruling
[`0006`](../decisions/0006-the-author-is-the-participant.md), which **struck the
non-author clause**: the operator directs, the agent builds, the operator tests
across the machines they hold, and *that chain* is the instrument this project
has. `0005`'s analysis stands; its refusal is overturned. **The population
question is closed in the other direction and is not re-litigated** — the
reopening trigger is at the foot of `0006` (fork > 0, or a second person running
socom unprompted).
⚠️ **2026-08-11: the trigger is now LIVE-ADJACENT and is the operator's to
call.** A second person — an engineer, not the author — ran socom on `buzz` and
reported back in writing. **Whether it was *unprompted* is `NOT OBSERVED`**
(field report §1: recruitment was not screened because nobody recruited), and
that word is the whole trigger. Do not re-litigate the population question from
a session; establish the fact or leave it open. `0008` deliberately does **not**
depend on it.

The run: repo `buzz` (Rust, `/home/akili`), build `a1cf0802daef` — **live
shipped code**, `cmp` byte-identical to the public artifact, not a local build.
**Stall point captured:** `socom gate fast` → `RED — checks.fast failed
(rc=127)`, `cargo: not found`. The participant did not recover inside the tool;
they escalated out of it. That is the datum the row asks for and it is on file.

## The second event — 2026-08-11, a non-author, and it is NOT a protocol run

`bench/exposure/2026-08-11-buzz-engineer-report.md`. An engineer installed socom
on `buzz` and wrote up what happened. **Read the sheet's header before leaning on
any of it:** there was no observer, no recruitment screen, no prohibition check,
and — the cell that cannot be reconstructed later — **no `socom version`
digest**. It is the strongest field evidence on file *and* weaker than a
conforming run. Both halves are true.

**The stall is the same one, third sighting:** `checks.fast` bound to
`cargo test`, `cargo` not on PATH, `cargo: not found`. **They recovered** — the
material difference from 2026-08-07, where the participant escalated out. They
rebound `checks.*` to `just` targets by hand and continued.

**Their diagnosis is exact and unprompted:** *"it checked whether a file existed,
not whether the command actually runs."* Verified: `install.py:255` is
`(root / "Cargo.toml").exists()`; `install.py:364` prints
`✓ … gates now run YOUR tests`; `shutil.which` is in this codebase and applied
correctly at `spawn.py:413` and `install.py:331` *(mechanism verified:
`grep -n shutil.which src/socom/*.py`)* — **the guard is inconsistently applied,
not missing.** Their charge lands on `verify-never-claim`,
`canon/constitution.xml:6`, **`rank="1"`**. That is `0008`.

⚠️ **Do NOT count their gate catch as evidence of value.** They planted a
formatting error deliberately to test the gate. §3 of the sheet excludes planted
defects by rule — *"3/5 of the agent cohort did exactly that and it produced zero
evidence of value."* It proves the **mechanism** works end-to-end when correctly
bound, which is the first such proof by a non-author, and it is **not** the
unstaged catch the row asks for. Do not let the two be conflated.

⚠️ **One repair of ours was confirmed in the field:** socom wrote
`CLAUDE.socom.md` rather than overwriting their `CLAUDE.md`, and they called it
out unprompted as the right call. That is the 2026-08-06 sidecar repair holding
up under a non-author.

## What the first run produced

**One finding produced a code change** — the first time an exposure run has.
`DEF-INSTALLED-BINARY-LANDS-INSIDE-THE-ADOPTED-REPO-01` was sighted a second
time, **without `PILOT.md` being followed**, which refuted the row's own
diagnosis (it blamed the doc's ordering). Repaired the same day at `f1dce80`:
`install` now **copies** and symlinks only for a dev checkout
(`_is_dev_checkout`, `install.py:48`) *(mechanism verified: `grep -n` — `:41`
`_is_socom_binary`, `:48` `_is_dev_checkout`, `:80` `cmd_install`)*, so the
download is disposable and socom prints the `rm` for it. Row is **DONE P1** with Changed + Pinned + Effect all
present *(measured: 4 of 10 new `tests/smoke.sh` §18 assertions FAIL against a
`git archive HEAD` of the pre-fix tree; `unit: 378 → 386`; acceptance re-run
whole on build `a1354b03b292`)*.

## What this session is for — read in this order

**Step 1 — DONE 2026-08-11, do not redo it.** `0008` was accepted by operator
ruling and **the repair shipped the same day** at `55d1397`: `_resolve_check`
gates the `✓ … gates now run YOUR tests` claim behind an actual resolution, the
exposure scenario reproduces honestly, `unit: 386 → 395`, and 9 of the 10
pre-fix-tree failures are those assertions. See `0008` §Repair.
⚠️ **`DEF-STATUS-CLAIMS-UNLABELLED-01` is STILL READY P1 and that is correct** —
one of seven surfaces is repaired; the other six stay held under `0001` rule 3
because `PILOT.md`'s *"did a metric mislead you?"* has six answers left to
collect. **Do not "finish the row."** `0008` §Scope is one surface and
§"counter-argument, kept" exists because a repair backlog reproduces the 6/6
pattern as easily as a feature backlog.

**Step 2. §5 — only on or after 2026-08-14.** Ask once, write the answer down.

> *"No obligation either way — did you end up running it again?"*

That wording is already on the sheet. **First use is compliance. Second use is
value.** §5 is binary, cheap and unfakeable, it is the headline metric, and it
is filled in a **separate sitting** a week after the run.
⚠️ **The 2026-08-11 field report does NOT fill it and does not replace it.** §5
asks whether **the operator** returned. The engineer is a different person and
carries their own, separately pending, §5 — see that sheet's §5 note on whether
it can be asked at all without contaminating it.

**Step 3 — DONE 2026-08-11.** The two field-report findings are filed as
`DEF-INDEX-COUNTS-THE-TOOL-NOT-THE-REPO-01` and
`DEF-HOOKS-COLLISION-IS-SILENT-AFTER-THE-FACT-01`, both **READY P1**, both
UNREPAIRED *(measured: `grep -nE '^- \`DEF-(INDEX-COUNTS|HOOKS-COLLISION)'`)*.
The hooks row is filed **narrower than the report framed it**: the guard behaved
correctly on the information it had, and the defect is the unwarned LATER
collision. Read the row before acting on the report's wording.

**So: if the date is before 2026-08-14, there is again NO WORK.** Steps 1 and 3
are done, everything in `buckets/build.md` is blocked, `0002` is still HELD, and
the ten remaining P1s are deliberately unrepaired — including the six surviving
surfaces of `DEF-STATUS-CLAIMS-UNLABELLED-01`. Say so and stop. **The 2026-08-11
session cleared the queue it was given; it did not license a new one.**

⚠️ **Do not fill §5 early.** A week is the measurement, not a formality. Asking
on day 2 measures politeness.
⚠️ **The in-session repeat of `socom compile` is NOT a second use** — same
sitting, and it was the step the rung meter had just instructed. The sheet says
so; do not re-litigate it.
⚠️ **Do not set the proof tier from this repo.** `0006` §"What this ruling does
not claim" declines to, and the `D0`/`D1` definition lives in
`/root/Akili/.claude/skills/root-gate` — **nothing here defines it**. The tier is
the operator's to set on the sheet's §6 line, against that definition.

**If the date is before 2026-08-14: there is no work.** Everything in
`buckets/build.md` is blocked on §5 *(measured: 1 READY + 8 BLOCKED)*, every P1
is deliberately unrepaired, and `0002` is HELD at the gate. The queue is empty
**by design**, not by accident. Say so and stop — a session that invents work to
fill the gap is the failure mode this whole file exists to prevent.

## Where the repo is

**Everything here is relative to `/root/socom`** — a SIBLING of `/root/Akili`,
not inside it. `cd /root/socom && git pull` first; check `pwd` before any edit.
Akili's `CLAUDE.md` does not govern here: no worktrees, no row claims, no `glab`,
no MRs. Commit **directly to `main`**, push, watch with `gh run watch`.
`bin/socom` is BUILT from `src/socom/*.py` — edit the source, run
`python3 build.py`, commit both (`python3 build.py --check` is a CI gate).
socom's own hooks are not wired in its checkout, so run `./bin/socom gate full`
yourself before every push.

**Four skills ship in this repo** and are auto-discovered — nothing to install
*(verified `d85381b`: `git ls-files .claude/skills/` lists all four)*.

- `ship-and-verify` — the push loop: `build.py` → `gate full` **by hand** →
  commit to `main` → `gh run watch` → **re-measure the public curl artifact**.
- `bucket-ledger-reconcile` — before writing ANY state table or flipping a row
  `DONE`. `DONE` = Changed + Pinned + Effect. Not "I edited it".
- `prompt-verify-pass` — mandatory at closeout and on any edit to this file.
  **Pass eleven exists because pass ten did not catch that its own premise had
  expired three commits earlier. Probe the premise, not only the numbers.**
- `reap-shells` — stale background shells; §5 covers socom's own reaper.

⚠️ **The doctrine skills were deliberately NOT ported** (root-gate,
residuality-gate, seam-coupling-gate, capability-composability-gate,
explain-plain). They live in `/root/Akili/.claude/skills/` and still govern. If
you need the tier vocabulary, read it there; do not re-derive it, and do not port
it as a side quest.

## Preflight — only if someone is about to run socom

30 seconds. A broken first touch burns a run on nothing.

```sh
curl -fsSL -o /tmp/socom.pre \
  https://raw.githubusercontent.com/Morse2580/socom/main/bin/socom \
  -w 'http=%{http_code} bytes=%{size_download}\n'
chmod +x /tmp/socom.pre && /tmp/socom.pre --help | head -3 && /tmp/socom.pre version
```

Re-measured 2026-08-11 after BOTH repairs shipped: `http=200`, **437237
bytes**, `cmp` byte-identical to `bin/socom`, build **`ad0cac783b19`**
*(measured: `curl -w` + `cmp` + `socom version` at `5eb8e81`)*. It moved twice
today — `bin/socom` had not changed since `f1dce80` before that. It MOVED — `bin/socom` changed for the
first time since `f1dce80`.
`--help` prints on **stdout, exit 0**, so `| head -3` truncates as written; bare
`socom` still exits 1 on stderr.
**Also confirm macOS/Linux/WSL** — native Windows is unsupported (`fcntl`).

⚠️ **This number changes on ANY merge touching `bin/socom`.** It has moved five
times across twelve passes *(measured: unchanged at the twelfth — `bin/socom`
last moved at `f1dce80`)*. Re-run the preflight; never carry it forward.
⚠️ **Record the `version` digest on the sheet.** It is a sha256 of the running
file, so it names the build a participant actually ran. A result that cannot name
its build is not reproducible evidence.

## Standing context — recorded so it is not re-derived

Each of these cost a session. None of them is work.

**`0007` + `INDEX.md` — landed 2026-08-10 on operator request. Analysis, not a
queue.** `0007` reads four external harness-engineering sources (Fowler/Böckeler
×2, Stripe minions, OpenAI Codex) against socom and decides what is adopted
**after §5**: a typed gate result, `guidance[]` wiring, a bounded attempt
budget — and what is refused outright (sidecar daemon, vendored sensors, the
devbox). Its load-bearing finding: every source's harness sits on an execution
environment its authors control; socom's bet is the inverse, and the 2026-08-07
`rc=127` stall is the price of that bet, not a bug in the gate code. External
claims are tagged `EXTERNAL`, never `MEASURED`, per `0003`'s precedent — and the
premise (whether a typed gate result changes what a participant does) is tagged
`UNMEASURED`, which is the shape that sank R1.
`INDEX.md` measures socom's own surface: 40 verbs, 7,378 lines of `src/`, and
**5 files of runtime state in the whole checkout** *(measured 2026-08-10 at
`083e844` — re-probe before quoting)*. The blackboard ref has carried **two rows
ever** — a lease and its release on the path `"--help"`, residue of the
flag-parsing bug at `cli.py:54`; zero `attest`, zero `findings`. `gate eval` is
RED because `.socom/ledger/` does not exist. Its diagnosis is **build order, not
drift**: every empty layer is second-order, and no workload has ever flowed
through socom. ⚠️ Its leverage ranking is an ORDERING for after §5 and
**authorises nothing** — §6 says so. Item 2 (self-adopt locally without
committing) and the `0001` enforcement-vs-detection question are both flagged
**for the operator**, not for a session.

**`decisions/0004` — the two boundaries socom does not represent.** Class A:
socom reports what it WROTE, not what took EFFECT (nine surfaces). Class B: socom
writes what it does not own, and no code represents "own" — `is_generated`
(`core.py:137`) *(mechanism verified: `grep -n` — `:137` is the `def
is_generated` line; `0004` cites it as `:141` and the prompt cited `:140`, both
now stale)* is the one place ownership IS tested and the one place socom
behaved correctly. `0002`'s class is their **intersection**, not a third thing.
The A/B is the strongest evidence on file for the metric row, **measured**: with
a detectable test command → `100% · T6`, `doctor clean`, `gate fast` RED; without
one → `33% · T2`, `doctor` exit 1. The right-hand column is socom working as
designed; the left is the defect, and it is the **common** case.
⚠️ The 2026-08-07 run added a **third** sign: detection *correct*
(`Cargo.toml` → `cargo test`), toolchain *absent*, `✓ gates now run YOUR tests`
printed anyway and refuted three commands later by rc=127. Appended to
`DEF-STATUS-CLAIMS-UNLABELLED-01`, not a new row.

**`decisions/0002` is HELD at the gate and must stay held.** The defect is D2;
the *fix* mechanism is D0 and cuts a shell/Python format contract, which the root
gate caps at D1. Do not build it. Step 1, when it is time, is a one-hour spike of
U1 alone *(hypothesis — operator-driven)*. **`0003` sharpened the spike
question:** `bb_do_claim` (`blackboard.py:520`) **already detects** the publish
failure and returns `published` + `publish_error` — the gap is **durability, not
detection**. But `log_breach` (`core.py:94`) writes a **local file**, and the
party the record exists to inform is a different session on a different machine
*(mechanism verified: `grep -n` — `bb_do_claim` at `blackboard.py:520`, `def
log_breach` at `core.py:94`; the prompt's old `:488` cite is stale)*. The question is
therefore: **can the writer half ship alone, or does a durable `published` flag
force the reader-side join immediately?** Answer it; do not assume it.

**`decisions/0003` — seven standards evaluated, none adopted, zero code.** No
standard can make a party you cannot execute inside enforce your policy
(SCITT/RFC 9943 has **zero** occurrences of `federat*`; §12 gives the relying
party the trust choice) *(not re-probed — primary-source verdict recorded in
`0003` with its citation; do not re-run the research to confirm it)*. The one surviving idea — SCITT §5.1.1.2, make the
registration checks reproducible — is already `canon/residuality.xml:95-99` in
socom's own words *(mechanism verified: `sed -n '95,99p'` is the
`compromise-recording` principle, "When you cannot prevent, record", with its
fail condition named)*. It is corroboration of the principle and an indictment of the
two open defects that violate it; it is **not evidence about socom**. git notes
is not the cheap move: it does not propagate, does not survive squash-merge, and
its local-add/separate-push shape reproduces the blackboard defect under a new
ref name.

**R1 — do not build it, and if you do, build it standalone.** The premise is
**REFUTED as a top-tier developer pain** *(not re-probed this pass — scout
finding of 2026-08-05, all three citations verified live at the time; treat as
carried, re-probe before leaning on it)*: no primary source where a developer
complains an instruction file told the agent something false. The loud,
repeatedly-sourced complaint is the mechanical inverse — agents *ignoring* rules
that are still correct (`anthropics/claude-code#15443`, `#37888`, Cursor forum).
Caveat kept: no survey has ever *asked*, so absence may be an availability
effect — you may not assume that. Prior art is PARTIAL (`giacomo/agents-lint`
ships **existence**-checking; git-history contradiction is its unreleased
roadmap). 18/19 corpus defects are `paired-parent`, so an existence-checker
scores ≈1/19 and cannot pass *(measured this pass: `tests/r1corpus.py` reports
"18 paired defects, 11 controls, 19 repos")*. Against Akili's 815-line
`CLAUDE.md`, only 13% of 576 statements name a checkable referent and actual
drift is ~0 *(not re-probed — measurement of 2026-08-04 against a repo outside
this tree)* — R1's hard problem is **precision, not detection**.

⚠️ **Open for the operator, NOT actioned:** the field evidence points at the
**enforcement** half rather than the **detection** half (R1), which contradicts
`0001`'s ratified ordering. Amending it is an operator decision, not a session's.
Counter-argument to keep: nobody has used the gates either, and the sweep showed
them bound to `pytest -q` on a Rust repo and `true` on a repo with no tests.

**`BUILD-ACP-RUNTIME-SEAM-01` (BLOCKED P2)** — filed at P1 on the argument that an
ACP proxy shape answers the entry-shape problem, **probed and refuted the same
day**: 3 of 8 gates are git-triggered and ACP has no `git commit`; `.socom/`
carries 17 state directories; the blackboard pushes by design *(not re-probed —
figures belong to the row's own `EVALUATED` block at `buckets/build.md:73`;
re-measure there before quoting them)*. The narrow seam survives (~3 d)
*(hypothesis — operator-driven)*. Read the row's `EVALUATED` block before acting on any of it.

**First-contact output was measured and DEFERRED, not fixed.** `quickstart` on a
fresh repo: **92 lines / 7.6 KB**, **33 absolute paths**, an ASCII logo, the rung
meter **twice** *(not re-probed — measured 2026-08-05 on build `1bc70ac4f16c`,
three builds ago; the baseline is kept as a HISTORICAL marker for that build and
must be re-measured on the current one before any before/after claim)*. Keep
those numbers — they are the pre-exposure baseline.
⚠️ Distinguish the halves: output VOLUME is not the finding; the ENTRY SHAPE it
describes **is** what §4 measures. The 2026-08-07 run hit the entry surface in
full — 11 `planted`, 15 `wrote`, `.gitignore` amended, `core.hooksPath` wired —
and recorded **no reaction**, so the scout's 2026-08-04 assessment is neither
confirmed nor refuted. ⚠️ **A React/Ink rewrite was REFUTED on its own goal**: it
was proposed to make install calmer and does the opposite — socom installs as ONE
curl'd stdlib-Python file, and Ink needs a Node runtime, so the 30-second
preflight above stops existing. If the CLI is ever restyled, it is restyled in
place.

## Do NOT do these

- **Do not re-run the exposure.** It ran 2026-08-07 and is recorded. `n=1` is
  what the root gate authorised. A second run before §5 is filled does not
  produce a nicer answer, it destroys the one measurement in flight.
- **Do not fill §5 before 2026-08-14**, and do not fill it in the same sitting as
  anything else. Separate sitting is the protocol.
- **Do not run another agent cohort.** Two ran (2026-08-03 cold-run ~30 defects;
  2026-08-05 5-substrate sweep, 3 P0s). Both were falsification; neither moved
  anything. Agents do not quit. A third buys nothing.
- **Do not work the P1 defects.** Eight are filed, all cheaper and more
  interesting than waiting, and they measure nothing.
  `DEF-STATUS-CLAIMS-UNLABELLED-01` is P1 **on purpose** — `PILOT.md` asks *"did
  a metric mislead you?"*, so repairing it first deletes a finding the sheet
  exists to collect (`0001` §Amendment 1 rule 3). The 2026-08-07 run generated
  exactly that finding, which is the rule working.
- **Do not repair either class in `decisions/0004` — including the cheap half.**
  The ~2h labelling column is IN-BUCKET and still HELD, because five of its six
  surfaces are what `PILOT.md` asks the participant.
- **Do not treat the install repair as licence to work the bucket.** It was
  repaired out of P1 order **on explicit operator instruction**, because the
  second sighting refuted the row's own diagnosis. That is a ruling, not a
  precedent a session may extend to itself.
- **Do not polish the `--help` or the wedge repairs.** Both landed with CI green
  and pre-fix-failing assertions. They are finished.
- **Do not build any capability.** Everything except R1 reads BLOCKED, and R1 is
  blocked on §5.
- **Do not adopt a standard, and do not re-run the standards research.** Reopens
  only at fork > 0.
- **Do not re-argue the population question.** `0005` closed it one way,
  **`0006` closed it the other way**, by operator ruling. It is closed. The one
  thing `0006` and `0005` both license is an **agent-behaviour A/B** (same repo,
  same task, one variable: socom present or absent) — author-runnable and
  explicitly **supporting, not blocking**. Run it by hand if you want it;
  **building** a harness for it is capability.

## State — measured 2026-08-11 at `d85381b`, re-probe anything you lean on

| Thing | State |
|---|---|
| socom `main` | `d85381b`, clean, pushed, CI **success @ `d85381b`** *(measured: `git log --oneline -1`, `git status --porcelain` = 0, `gh run list -L1`)*. `git log --oneline -3` and re-probe rather than trusting this SHA. |
| Buckets | `defects.md` **9 DONE P0 + 0 READY P0 + 2 DONE P1 + 10 READY P1** *(measured: 9/0/2/10 via `grep -cE`)* · `build.md` 1 READY (R1) + 8 BLOCKED *(measured: 1/8)* · `evidence.md` `EV-NONAUTHOR-EXPOSURE-01` **READY P0 — run recorded, §5 pending** *(L15 @ `d85381b`)* |
| Exposure | **TWO events on file** *(measured: `ls bench/exposure/` = README + TEMPLATE + **two** dated sheets)*. (1) **RUN 2026-08-07** — `2026-08-07-akili.md`, protocol-conforming, §1-§4/§6/§7 filled, **§5 PENDING until 2026-08-14**. (2) **FIELD REPORT 2026-08-11** — `2026-08-11-buzz-engineer-report.md`, a **non-author** engineer on `buzz`; ⚠️ **not a protocol run** (no observer, no recruitment screen, **no `socom version` digest**) and its own §5 is separately PENDING |
| Proof tier | **operator to set** — `0006` declines to derive it and this repo does not define `D0`/`D1`. This prompt asserts no tier. |
| Suite | `unit: 399 passed, 0 failed` · `r1corpus: 146 passed, 0 failed` · `gate full: PASS` · `build.py --check` clean *(measured: all four re-run 2026-08-11 after the repair)* |
| Artifact | http=200, **437237** bytes, build **`ad0cac783b19`**, `cmp` byte-identical to `bin/socom` *(measured 2026-08-11 after the `0008` repair shipped)*. ⚠️ **Re-measure — never carry.** |
| Decisions | `0001` exposure-before-capability · `0002` unresolvable-enforcement-must-record (**HELD**) · `0003` no-standard-binds-a-fork · `0004` two-boundaries-socom-does-not-represent · `0005` the-user-is-an-agent-the-adopter-is-not · `0006` the-author-is-the-participant (Accepted) · `0007` adopt-the-sensor-contract-not-the-sensor (Proposed — BLOCKED on §5) · **`0008` the-guess-must-resolve-before-it-is-claimed (Accepted 2026-08-11 — REPAIRED, surface 1 of 7)** *(measured: 8 files; `sed -n '3p' decisions/0008-*.md`)* |
| Analysis landed 2026-08-10/11 | `0007` + `INDEX.md` — operator-requested, **authorise nothing**. `INDEX.md` item 2 was run, **refuted** (adopt produces no ledger) and **withdrawn by operator ruling**; item 1b records the operator's ask to be given repos to test, **gated behind §5** |
| `0008` — closed | **Accepted and REPAIRED 2026-08-11** at `55d1397`. One surface of `DEF-STATUS-CLAIMS-UNLABELLED-01`; the row stays **READY P1** with six surfaces held. ⚠️ **Do not finish the row** |

Probes: `./bin/socom gate full` · `python3 build.py --check` ·
`python3 tests/unit.py` · `python3 tests/r1corpus.py` · `grep -c '^- \`' buckets/*.md`

## The bound

Ten passes of this file closed with *"only the run moves it."* The run happened,
and it moved one thing: a P1 got repaired because a finding refuted its diagnosis.
It did **not** move the proof tier, because §5 — the metric — is unfilled.

A result of *"never ran it again"* closes the row exactly as a positive result
would. It is not a failed session.

**One question. 2026-08-14. Then write down the answer.**
