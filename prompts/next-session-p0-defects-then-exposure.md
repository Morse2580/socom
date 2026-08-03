# Next session — repair the four P0 defects, then run the exposure measurement

**Rows:** `DEF-HOOKS-HIJACK-NO-UNADOPT-01`, `DEF-COMMIT-GATE-REJECTS-HOST-CONVENTION-01`,
`DEF-ADOPTION-REDDENS-HOST-GATE-01`, `DEF-RUNTIME-STATE-UNIGNORED-01` — all
**READY P0** in `buckets/defects.md`.
**Governed by:** `decisions/0001-exposure-before-capability.md` + **§Amendment 1**.

## Where the repo is — read this first

**Everything in this prompt is relative to `/root/socom`.** Start there:

```sh
cd /root/socom && git pull            # remote: github.com/Morse2580/socom.git, branch main
# not present? →  git clone https://github.com/Morse2580/socom.git /root/socom
```

⚠️ **socom is a SIBLING of `/root/Akili`, not inside it.** A session often opens
in `/root/Akili` by default; every path below (`buckets/`, `src/socom/`,
`bin/socom`, `prompts/`) is a socom path and will silently resolve to the wrong
place — or to nothing — if you are still in the Akili checkout. Check `pwd`
before your first edit.

⚠️ **Akili's `CLAUDE.md` does not govern here, and socom has no `CLAUDE.md` of
its own.** Do not apply Akili's session ritual to this repo — there are **no**
worktrees, no `scripts/ops/session-claim.sh` row claims, no `glab`, no merge
trains, no MR, and no `thoughts/shared/buckets/`. socom's own conventions:

| | socom |
|---|---|
| Task state | `buckets/{defects,build,evidence}.md` at the repo root |
| Decisions | `decisions/NNNN-*.md` |
| Landing work | commit **directly to `main`** and `git push origin main` |
| CI | GitHub Actions (`.github/workflows/ci.yml`), watch with `gh run watch` |
| Gate | `./bin/socom gate full` + `python3 build.py --check` |

⚠️ **`bin/socom` is a BUILT artifact** assembled from `src/socom/*.py` by
`build.py`. Edit `src/socom/`, never `bin/socom` — then run `python3 build.py`
and commit both. `python3 build.py --check` is a CI gate and fails on drift.

⚠️ **socom's git hooks are not wired in its own checkout** (`core.hooksPath` is
unset), so nothing runs your gates on commit. Run `./bin/socom gate full`
yourself before every push; CI is the only other thing that will catch you.

This is socom work — **do not open an Akili MR for it.**

## The one thing this session is for

Repair the four P0 defects **and then run `EV-NONAUTHOR-EXPOSURE-01`.**

The four exist for exactly one reason: so the exposure run does not spend a
scarce participant discovering a defect that is already written down. They are
not the work. **The exposure measurement is the work**, and it has been P0 and
unrun since 2026-08-01.

If you repair four defects and do not run the exposure measurement, this session
was the seventh artifact.

## The four, in order

Each is bounded to **repair only** — behaviour socom already ships and already
claims. Anything that adds a surface is a capability and is already filed
`BLOCKED` in `buckets/build.md`. Read the row before you touch the code; each
carries its verified evidence.

1. **`DEF-HOOKS-HIJACK-NO-UNADOPT-01`** — `src/socom/lifecycle.py:379`
   `_wire_hooks` (the overwrite is the bare `git config core.hooksPath` at
   `:387`) replaces the adopter's value unconditionally, silently disabling
   husky / lefthook / any existing hooks. `cmd_uninstall` (`install.py:83`)
   removes only the bin symlink; there is no `unadopt`, and the prior value was
   never recorded so it cannot be restored even in principle. **Start here** —
   it is the only one that makes the adopter's own gates silently *pass*, and it
   falsifies `PILOT.md`'s bolded "additive and non-destructive" claim.

2. **`DEF-ADOPTION-REDDENS-HOST-GATE-01`** — quickstart binds gates to the repo's
   test command, then its own emitted files fail it. Verified on zustand: 16
   files listed by `prettier --list-different`, all 16 socom-authored, on a
   pristine checkout that was green before.

3. **`DEF-COMMIT-GATE-REJECTS-HOST-CONVENTION-01`** — `gate.py:62` `COMMIT_RX`
   rejects 60 of zustand's last 100 upstream subjects. Widen to the
   conventional-commit set with an optional scope, **and print the rule that
   fired** — today the error names a format the rejected subject already
   satisfies. Making the set configurable is a knob → already `BLOCKED`.

4. **`DEF-RUNTIME-STATE-UNIGNORED-01`** — socom never touches `.gitignore` on any
   path (`grep -rn gitignore src/socom/ templates/` → zero hits), so per-PID lease
   shards, the breach log and the index blobs are one `git add -A` from a commit.

## Then the thing that actually matters

`EV-NONAUTHOR-EXPOSURE-01`: five engineers who are not the author, one run each,
`PILOT.md` as it stands, recorded stall points, and a yes/no per participant on
**voluntary second use**. First use is compliance; second use is value.

⚠️ **Do not demo it to them.** ⚠️ **Do not recruit only people who owe you a
favour.** ⚠️ **Do not improve `PILOT.md` first** — where it confuses a stranger
IS the finding.

**"Five people, zero second uses" is a valid and complete result.** It is the
kill signal the Phase 3a trial cannot produce.

## Do NOT do these

- **Do not work the P1 defects.** Four are filed and they are cheaper and more
  interesting than the P0s. They measure nothing. `DEF-STATUS-CLAIMS-UNLABELLED-01`
  in particular is P1 **on purpose**: `PILOT.md`'s report list asks *"did a metric
  mislead you?"*, so repairing the misleading metric before the run **deletes a
  finding the five participants are supposed to generate** (0001 §Amendment 1
  rule 3).
- **Do not build any capability.** Every row in `buckets/build.md` except
  `R1-INTENT-DRIFT-DETECTOR-01` reads `BLOCKED` on the exposure row. That clause
  is 0001's falsifiable acceptance and is checkable by reading the file.
- **Do not run another agent cold-run cohort.** One was run 2026-08-03. It is
  productive and it **cannot move the D-tier** — see the ⚠️ inside
  `EV-NONAUTHOR-EXPOSURE-01`. Reaching for it again instead of the real row is
  proxy selection.
- **Do not write R1.** Its corpus exists (`bench/r1-corpus/`, 30 records) and the
  ordering is enforced by `tests/r1corpus.py`. R1 is permitted, but it is not
  this session.

## State — verified 2026-08-03, re-probe anything you lean on

| Thing | State |
|---|---|
| socom `main` | `c58bd26` — defect lane + 12 rows |
| Buckets | `defects.md` (8 rows, 0 DONE) · `build.md` (9 rows, 1 READY) · `evidence.md` (4 rows, 1 DONE) |
| Proof tier | **D0 — ASSUMED**, unchanged since 2026-08-01 |
| R1 corpus | `bench/r1-corpus/corpus.jsonl`, 30 records, 18 paired defects, 19 repos |
| CI | `.github/workflows/ci.yml`; `python3 build.py --check` + `./bin/socom gate full` |

Probes: `./bin/socom gate full` · `python3 build.py --check` ·
`python3 tests/r1corpus.py` · `grep -c '^- \`' buckets/*.md`

## The bound

Twelve rows were filed on 2026-08-03 from a cohort that found ~30 defects. None
of it moved the proof tier, because none of it could. Six artifacts, five months,
zero non-author users — and the row that would change that has now been available
for three days.

Repair four things. Then go find five people.
