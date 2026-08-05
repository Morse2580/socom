<!--
CLAIM-VERIFY PASS — 2026-08-05, probed against the tree at the SHA below.
Every concrete claim in this prompt was re-run, not carried over.
  VERIFIED  socom main SHA + clean tree ......... git rev-parse / status
  VERIFIED  buckets: 4 DONE P0 / 6 READY P1 ..... grep -cE '^- `DEF-.*(DONE P0|READY P1)'
  VERIFIED  build.md 1 READY + 7 BLOCKED ........ grep -cE '^- `.*(READY|BLOCKED)'
  VERIFIED  EV-NONAUTHOR-EXPOSURE-01 READY P0 ... grep, still unrun
  VERIFIED  bench/exposure/{README,TEMPLATE}.md . ls
  VERIFIED  decisions/0001 + 0002 ............... ls
  VERIFIED  unit 339 passed / r1corpus 146 ...... python3 tests/{unit,r1corpus}.py
  VERIFIED  public curl URL 200, 408964 bytes ... curl -w, cmp against bin/socom
  VERIFIED  proof tier D0, unchanged ............ bench/exposure/ holds the template only
  REWRITTEN row headline read "five engineers" .. reconciled to n=1 this session
  HYPOTHESIS none.
-->

# Next session — stop building. Run the n=1 exposure.

**Row:** `EV-NONAUTHOR-EXPOSURE-01` (`buckets/evidence.md`), **READY P0**, `n=1`.
**Governed by** `decisions/0001-exposure-before-capability.md`.
**Record it on the sheet:** copy `bench/exposure/TEMPLATE.md` to
`bench/exposure/<YYYY-MM-DD>-<handle>.md`.

## Where the repo is

**Everything here is relative to `/root/socom`** — a SIBLING of `/root/Akili`,
not inside it. `cd /root/socom && git pull` first; check `pwd` before any edit.
Akili's `CLAUDE.md` does not govern here: no worktrees, no row claims, no `glab`,
no MRs. Commit **directly to `main`**, push, watch with `gh run watch`.
`bin/socom` is BUILT from `src/socom/*.py` — edit the source, run
`python3 build.py`, commit both (`python3 build.py --check` is a CI gate).
socom's own hooks are not wired in its checkout, so run `./bin/socom gate full`
yourself before every push.

## The one thing this session is for

**Put socom in front of one engineer who is not the author, watch in silence,
write down where they stop.** That is the whole session. It is not a coding task
and there is no code deliverable.

The root gate authorised exactly this — *"one non-author engineer, observed"* —
and it has never been done. Five months, six artifacts, zero non-author users,
proof tier **D0**. Every capability row in `buckets/build.md` is BLOCKED on it.

**Everything you need is already prepared.** `bench/exposure/README.md` is the
protocol (recruit → ask → session → record → the one-week second-use check) and
`TEMPLATE.md` is the observer's sheet. Read the README once and run it. Do not
re-derive the protocol, and do not improve the sheet instead of using it.

⚠️ Do not demo it. ⚠️ Do not fix `PILOT.md` first — where it confuses a stranger
IS the finding. ⚠️ Do not substitute an agent: agents can falsify but cannot
confirm, and one cohort already ran (2026-08-03). ⚠️ Do not recruit someone who
owes you a favour — politeness produces a first use and never a second, and
second use is the metric.

**Preflight, 30 seconds, before the session** (a broken first touch burns a
scarce participant on nothing):

```sh
curl -fsSL -o /tmp/socom.pre \
  https://raw.githubusercontent.com/Morse2580/socom/main/bin/socom \
  -w 'http=%{http_code} bytes=%{size_download}\n'
chmod +x /tmp/socom.pre && /tmp/socom.pre --help | head -3
```

Verified 2026-08-05: `http=200`, 408964 bytes, byte-identical to `bin/socom`,
`--help` prints the command list. **Also confirm the participant is on
macOS/Linux/WSL** — native Windows is unsupported and finding out mid-session
wastes the run.

## What changed on 2026-08-05

A class sweep, no code. Two rows filed, **neither repairable-first and neither
able to fire at `n=1`**:

- `DEF-UNRESOLVABLE-GATE-LEAVES-NO-TRACE-01` — when a gate cannot run at all,
  socom records nothing, so a repo whose `core.hooksPath` still declares socom's
  gates commits ungated indefinitely and no socom surface can say so. Needs the
  downloaded file moved or cleaned *after* install — takes days.
- `DEF-BLACKBOARD-GRANTS-ON-UNREACHABLE-REMOTE-01` — **highest-severity P1.**
  With an unreachable remote, `claim` **grants** a lease it would have refused,
  and the record it writes is byte-identical to a published one. Measured: two
  sessions both holding the same path, each `--scan` reporting itself as sole
  holder. Needs two concurrent sessions.

The class both share: *enforcement whose declaration is durable, whose capability
resolves through a referent socom does not own, and whose resolution failure
degrades open without a trace* — which socom's own `canon/residuality.xml`
`compromise-recording` names, and the code fails. Full sweep (6 instances, 6
sites checked clean, 2 bounded residues) is the appendix of
`decisions/0002-unresolvable-enforcement-must-record.md`.

**0002 is HELD at the gate and must stay held.** The defect is D2; the *fix*
mechanism is D0 and cuts a shell/Python format contract, which the root gate caps
at D1. Do not build it. When it is time, step 1 is a one-hour spike of U1 alone.

⚠️ **The blackboard defect also breaks Phase 3a's instrument.** That trial needs
3+ concurrent people — exactly when it fires — so a low tally could not
distinguish "thesis wrong" from "a participant's remote was refusing and their
leases were invisible." Cross-referenced into `EV-TRIAL-PROTOCOL-CONFOUND-01`.
It does **not** block the n=1 exposure.

## The three assessments that should still weaken the instinct to build

1. **Build order/shape (scout, 2026-08-04).** Execution is rigorous; the *order*
   and *entry shape* are wrong for the population socom needs. Planting ~32 files
   and rewriting `core.hooksPath` spends first-contact trust before earning any.
   §4 of the recording sheet now captures the participant's reaction to exactly
   this — free, and it confirms or refutes the assessment.
2. **The adoption model contaminates its own experiment.** A stranger cannot
   evaluate "is drift-detection useful" without also absorbing "will this rewrite
   my git hooks." Two hypotheses, one test, inseparable result.
3. **R1 measured, not guessed.** Against Akili's 815-line `CLAUDE.md`, only 13%
   of 576 statements name a checkable referent, and actual drift is ~0. R1's hard
   problem is precision, not detection.

## Do NOT do these

- **Do not work the P1 defects.** Six are filed now, all cheaper and more
  interesting than the exposure, and they measure nothing.
  `DEF-STATUS-CLAIMS-UNLABELLED-01` is P1 **on purpose** — `PILOT.md` asks *"did
  a metric mislead you?"*, so repairing it first deletes a finding the
  participant is meant to generate (`0001` §Amendment 1 rule 3).
- **Do not build any capability.** Everything except R1 reads BLOCKED.
- **Do not build R1 either**, unless the exposure has happened. If you do, ship
  it **standalone** — own binary, zero adoption, zero git-config writes, no
  `.socom/` — so the two hypotheses stay separable.
- **Do not run another agent cohort.** It cannot move the D-tier.
- **Do not run a second participant to get a nicer answer.** `n=1` is what the
  root gate authorised; a confident *yes* is what §14.4's five-after-R1 is for.

## Cheaper alternative if no engineer is reachable this week

Test the *premise* instead of the tool: ask three engineers to describe their
last painful session driving AI agents on a real repo. Twenty minutes each, no
install, no `PILOT.md`. If the pain they describe is not the pain socom
addresses, tool quality is irrelevant and that is worth knowing before R1.

## State — verified 2026-08-05, re-probe anything you lean on

| Thing | State |
|---|---|
| socom `main` | state below verified at `fa432bb`; the closeout commit that landed this prompt sits on top of it. `git log --oneline -3` and re-probe rather than trusting either SHA. Clean, pushed, CI green. |
| Buckets | `defects.md` 4 DONE P0 + **6** READY P1 · `build.md` 1 READY (R1) + 7 BLOCKED · `evidence.md` `EV-NONAUTHOR-EXPOSURE-01` READY P0, **unrun** |
| Proof tier | **D0 — ASSUMED**, unchanged since 2026-08-01 |
| Suite | `unit: 339 passed, 0 failed` · `r1corpus: 146 passed, 0 failed` · `gate full: PASS` · `build.py --check` clean |
| Exposure prep | `bench/exposure/{README,TEMPLATE}.md` landed; download URL preflighted |

Probes: `./bin/socom gate full` · `python3 build.py --check` ·
`python3 tests/unit.py` · `python3 tests/r1corpus.py` · `grep -c '^- \`' buckets/*.md`

## The bound

The tool is less broken than it was, the class behind two of its defects is now
named and swept, and the recording sheet is written. **None of that moved the
proof tier, because none of it is the blocking claim.**

A result of *"one person, stopped at step 2, never ran it again"* closes the row
exactly as a positive result would. It is not a failed session.

**One engineer. This week. Watch in silence.**
