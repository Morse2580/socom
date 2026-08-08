<!--
CLAIM-VERIFY PASS — history. Every pass re-ran its claims; none were carried.
Passes 1-10 (2026-08-05 → 2026-08-06) are compacted to their standing verdicts:
  the byte count and build digest move on ANY merge touching `bin/socom` and
  must be re-measured every pass (Regression Test 1, hit three times);
  every `file.py:N` in this prompt is stale by the next edit — re-`sed` it, the
  SYMBOL is the durable cite (Regression Test 3);
  nine P0 repairs across those ten passes moved the proof tier by NOTHING.
Full pass-by-pass history: `git log -p prompts/next-session-run-n1-exposure.md`.

REWRITTEN 2026-08-08 (ELEVENTH pass, at `f1dce80`). **This pass refutes the
premise of the ten before it.** The prompt said the exposure was UNRUN and that
running it was the whole session. The repo says otherwise: the run happened on
2026-08-07, three commits after the tenth pass wrote this file. Every line below
was re-run today, not carried.
  REWRITTEN THE RUN ......... **HAPPENED — 2026-08-07**,
            `bench/exposure/2026-08-07-akili.md` *(measured: `ls bench/exposure/`
            — README + TEMPLATE + one dated sheet)*. The ten previous passes all
            closed with "only the run moves it". It moved.
  REWRITTEN population ...... **`0006` STRUCK the non-author clause** by operator
            ruling. The author IS the participant *(verified `f1dce80`:
            `decisions/0006-the-author-is-the-participant.md`, Status Accepted
            2026-08-07)*. `0005`'s refusal is overturned; its analysis stands.
  REWRITTEN decisions ....... 0001-0005 -> **0001-0006** *(measured: 6 files)*
  REWRITTEN defects ......... 9 DONE P0 / 0 READY P0 / **1 DONE P1** / **8**
            READY P1 *(measured: 9/0/1/8 via `grep -cE`)*. Was 9/0/0/9 — one P1
            flipped DONE, see below.
  REWRITTEN public artifact . 430621 -> **434361** bytes, `a1cf0802daef` ->
            **`a1354b03b292`**, http=200, `cmp` byte-identical to `bin/socom`
            *(measured: `curl -w` + `cmp` + `/tmp/socom.pre version`)*. Moved
            because `f1dce80` touched `bin/socom`. Regression Test 1 again.
  REWRITTEN suites .......... unit 378 -> **386** / r1corpus 146 / gate full
            PASS / `build.py --check` clean / CI **success @ `f1dce80`**
            *(measured: all five re-run at `f1dce80`)*
  REWRITTEN code cites ...... two cites in the old body were stale and would
            have resolved to real, wrong lines: `bb_do_claim` `blackboard.py:488`
            -> **`:520`**; `is_generated` `core.py:140` -> **`:137`**. Re-`sed`
            before quoting anything below.
  VERIFIED  build.md ........ 1 READY (R1) + 8 BLOCKED, unchanged *(measured: 1/8)*
  VERIFIED  EV row .......... `EV-NONAUTHOR-EXPOSURE-01` still **READY P0** —
            correctly, because §5 is unfilled *(L15 @ `f1dce80`)*
  VERIFIED  proof tier ...... **operator to set** — `0006` §"does not claim"
            explicitly declines to derive it, and the `D0`/`D1` vocabulary is
            not defined in this repo. This prompt does NOT assert a tier.
  HYPOTHESIS none.

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

# Next session — fill §5 of the exposure sheet. Not before 2026-08-14.

> ⚠️ **The filename is historical.** It says "run-n1-exposure"; the run happened
> on 2026-08-07. The name is kept because eleven verify passes of audit trail
> live in this file's history and `prompt-verify-pass` globs
> `prompts/next-session-*.md`. Same convention `0006` used for the row ID.

**Row:** `EV-NONAUTHOR-EXPOSURE-01` (`buckets/evidence.md`), **READY P0**, `n=1`
*(L15 @ `f1dce80`)*.
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

The run: repo `buzz` (Rust, `/home/akili`), build `a1cf0802daef` — **live
shipped code**, `cmp` byte-identical to the public artifact, not a local build.
**Stall point captured:** `socom gate fast` → `RED — checks.fast failed
(rc=127)`, `cargo: not found`. The participant did not recover inside the tool;
they escalated out of it. That is the datum the row asks for and it is on file.

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

## The one thing this session is for

**Nothing, until 2026-08-14.** Then: ask the §5 question, once, and write down
the answer.

> *"No obligation either way — did you end up running it again?"*

That wording is already on the sheet. **First use is compliance. Second use is
value.** §5 is binary, cheap and unfakeable, and it is the headline metric —
which is why it is filled in a **separate sitting**, a week after the run, and
not today.

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
*(verified `f1dce80`: `git ls-files .claude/skills/` lists all four)*.

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

Verified 2026-08-08 at `f1dce80`: `http=200`, **434361 bytes**, `cmp`
byte-identical to `bin/socom`, build **`a1354b03b292`** (last commit touching
`bin/socom`: `f1dce80`) *(measured: `curl -w` + `cmp` + `socom version`)*.
`--help` prints on **stdout, exit 0**, so `| head -3` truncates as written; bare
`socom` still exits 1 on stderr.
**Also confirm macOS/Linux/WSL** — native Windows is unsupported (`fcntl`).

⚠️ **This number changes on ANY merge touching `bin/socom`.** It has moved five
times across eleven passes. Re-run the preflight; never carry it forward.
⚠️ **Record the `version` digest on the sheet.** It is a sha256 of the running
file, so it names the build a participant actually ran. A result that cannot name
its build is not reproducible evidence.

## Standing context — recorded so it is not re-derived

Each of these cost a session. None of them is work.

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

## State — measured 2026-08-08 at `f1dce80`, re-probe anything you lean on

| Thing | State |
|---|---|
| socom `main` | `f1dce80`, clean, pushed, CI **success** *(measured: `gh run list`)*. `git log --oneline -3` and re-probe rather than trusting this SHA. |
| Buckets | `defects.md` **9 DONE P0 + 0 READY P0 + 1 DONE P1 + 8 READY P1** *(measured: 9/0/1/8 via `grep -cE`)* · `build.md` 1 READY (R1) + 8 BLOCKED *(measured: 1/8)* · `evidence.md` `EV-NONAUTHOR-EXPOSURE-01` **READY P0 — run recorded, §5 pending** *(L15 @ `f1dce80`)* |
| Exposure | **RUN 2026-08-07** — `bench/exposure/2026-08-07-akili.md` *(measured: `ls bench/exposure/` = README + TEMPLATE + one dated sheet)*. §1-§4, §6, §7 filled; **§5 PENDING until 2026-08-14** |
| Proof tier | **operator to set** — `0006` declines to derive it and this repo does not define `D0`/`D1`. This prompt asserts no tier. |
| Suite | `unit: 386 passed, 0 failed` · `r1corpus: 146 passed, 0 failed` · `gate full: PASS` · `build.py --check` clean *(measured: all four re-run at `f1dce80`)* |
| Artifact | http=200, **434361** bytes, build **`a1354b03b292`**, `cmp` byte-identical to `bin/socom` *(measured at `f1dce80`)*. ⚠️ **Re-measure — never carry.** |
| Decisions | `0001` exposure-before-capability · `0002` unresolvable-enforcement-must-record (**HELD**) · `0003` no-standard-binds-a-fork · `0004` two-boundaries-socom-does-not-represent · `0005` the-user-is-an-agent-the-adopter-is-not · **`0006` the-author-is-the-participant (Accepted — supersedes `0005`'s disposition)** *(measured: 6 files)* |

Probes: `./bin/socom gate full` · `python3 build.py --check` ·
`python3 tests/unit.py` · `python3 tests/r1corpus.py` · `grep -c '^- \`' buckets/*.md`

## The bound

Ten passes of this file closed with *"only the run moves it."* The run happened,
and it moved one thing: a P1 got repaired because a finding refuted its diagnosis.
It did **not** move the proof tier, because §5 — the metric — is unfilled.

A result of *"never ran it again"* closes the row exactly as a positive result
would. It is not a failed session.

**One question. 2026-08-14. Then write down the answer.**
