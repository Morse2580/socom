# Next session — build R1's acceptance corpus, before R1 exists

**Row:** `EV-R1-ACCEPTANCE-CORPUS-01` (READY, P1) in `buckets/evidence.md`.
**Governed by:** `decisions/0001-exposure-before-capability.md`.
**Repo:** socom (`github.com/Morse2580/socom`). This is socom work — do not open
an Akili MR for it.

## The one thing this session is for

Assemble the corpus that decides whether R1 works, **and commit it before a
single line of R1 exists.** The git-log ordering is itself the proof that the
detector was not tuned to pass its own test. If you write R1 first, the corpus
is worthless no matter how good it looks.

**Goal, stated once:** turn *"R1 works"* from an opinion into a number —
*finds N of M real drift defects, reports nothing on clean repos, and extracted
K>0 assertions while doing it.* That sentence is the only thing that makes
`EV-NONAUTHOR-EXPOSURE-01` interpretable rather than a vibe.

## Mine, do not plant

A commit that renamed a build command without updating `CLAUDE.md` is a genuine
intent-drift defect, and **its parent commit is a free, perfect control** — same
repo, same config, one difference, and not chosen by the person writing the
detector.

Planting biases the corpus toward defects you already know R1 will catch. That
bias is invisible afterwards and it is the whole reason this row exists.

⚠️ **Synthetic repos are worthless here.** The defect class is *"config drifted
away from a real codebase over months."* A freshly generated fixture cannot
exhibit it — there is no drift without elapsed time.

## The five control classes — all required

| Control | Catches | Cost |
|---|---|---|
| **Paired parent** — the same repo one commit before the drift | everything; attributes the finding to the defect and nothing else | free from history |
| **Honest config** — real repo, accurate declarations, R1 must report zero | flags-everything | find one |
| **Non-vacuity** — assert R1 extracted **>0 assertions** from that honest repo | ⚠️ **the killer** | an assertion, not a repo |
| **Near-miss** — command exists only via Makefile/alias/wrapper · path gitignored but present · "never edit X" where X was edited *before* the rule landed · a command name in prose, not declared | anchoring + temporal traps | hand-pick |
| **No config / pure prose** — nothing checkable exists | R1 must say "nothing to check" *distinguishably* from "checked, clean" | trivial |

**Non-vacuity is the one that gets skipped, and it is the one that matters.** An
honest-config control alone cannot distinguish *"parsed the config and found it
truthful"* from *"parsed nothing at all"* — both emit zero findings. A parser
that understands none of the file passes every clean-repo test you can write.
Record the assertion count, not just the finding count.

## Precision over recall

A detector that flags everything scores 100% against defects alone. `PILOT.md`
already names the killer: *"Did a gate fire a FALSE POSITIVE? Even one on a bad
day kills adoption."* R1 parses, and parsing can be wrong. A tool that reports
three lies in a stranger's config and gets one wrong is uninstalled that
afternoon.

## Where to mine

Repos that carry `CLAUDE.md` / `AGENTS.md` / `.cursor/rules` **and** have enough
history for the config to have rotted. Search GitHub for those filenames, then
look for commits that renamed a script, moved a path, or retired a tool without
touching the config in the same commit.

**A verified live exemplar to calibrate against** — Akili `main` `7c6845288`,
`docs/ERROR_INDEX.md:5-7`:

> *"This file is auto-generated from the akili-graph. Do NOT edit manually. Run
> `scripts/generate-error-index.sh` to regenerate."*

`scripts/generate-error-index.sh` does not exist in that tree
(`git cat-file -e origin/main:scripts/generate-error-index.sh` → absent). That
is textbook R1: a declared command that is not there. Use it to sanity-check
what you are hunting for — but ⚠️ **do not let the corpus become all-Akili.**
One repo's idiom is one repo's idiom, and R1 has to survive a stranger's.

## Scope — what this session does NOT do

- **Do not write R1.** Not a prototype, not a spike, not "just to see." The
  ordering is the point.
- **Do not plant defects.**
- **Do not touch the blackboard** or any candidate increment — all `BLOCKED` on
  `EV-NONAUTHOR-EXPOSURE-01` per decision 0001.
- **Do not improve `PILOT.md`.** Where it confuses a stranger IS the finding for
  `EV-NONAUTHOR-EXPOSURE-01`.

## Falsifiable acceptance

≥10 mined defects, each with its paired parent commit; every defect
independently confirmed present by a **recorded command and its output**; at
least one instance of each of the other four control classes; and the whole
corpus committed **before any R1 code** — checkable by `git log` ordering.

## State — verified 2026-08-03, re-probe anything you lean on

| Thing | State |
|---|---|
| socom `main` | `3664d4d` — decision 0001 + buckets + the amended corpus row |
| Akili `main` | `7c6845288` |
| Buckets | `buckets/evidence.md` (4 rows, **0 DONE**), `buckets/build.md` (5 rows) |
| Proof tier | **D0 — ASSUMED**, unchanged since 2026-08-01 |
| Blackboard trial | day 2 of 14; tally 2 entries — 1×C, 1×B, **zero A**; demoted to an instrument |
| CI | `.github/workflows/ci.yml`; `python3 build.py --check` + `./bin/socom gate full` must both pass |

Probes: `./bin/socom gate full` · `python3 build.py --check` ·
`grep -c '^- `' buckets/*.md`

## The thing this row does not do

The corpus makes R1 **gradeable**. It does not make anyone **want** it. The P0
is still `EV-NONAUTHOR-EXPOSURE-01` — five engineers who are not the author —
and no session can do it, because it needs people rather than agent time. It has
been available since 2026-08-01 and is still unrun. Do not let a productive
corpus session read as progress on the thing that is actually blocking.
