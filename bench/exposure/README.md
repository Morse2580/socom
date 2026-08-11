# bench/exposure — the non-author exposure runs

The recording surface for [[EV-NONAUTHOR-EXPOSURE-01]] (`buckets/evidence.md`),
governed by [`decisions/0001`](../../decisions/0001-exposure-before-capability.md).

This is the **only** directory in the repo whose contents can move the proof tier
off **D0 — ASSUMED**. Everything in `buckets/build.md` is blocked on a file
landing here.

## What this measures, and what it does not

| | |
|---|---|
| **Measures** | where a non-author stops · whether a bound gate caught something real, unstaged · **whether they ran a socom verb again without being asked** |
| **Does not measure** | whether socom is well-built · whether the participant liked it · whether the author could explain it |

**First use is compliance. Second use is value.** The headline metric is the
second one, and it is binary, cheap and unfakeable.

## Running one

1. Copy `TEMPLATE.md` to `<YYYY-MM-DD>-<participant-handle>.md`.
2. Fill §1 **before** the session. Everything else is filled live or after.
3. **Confirm the participant is standing in a repository before they run
   anything** — `git rev-parse --show-toplevel` must print the repo they mean to
   adopt. This is silent setup, like handing someone a laptop; say nothing about
   socom while you do it.
4. §5 is filled **one week later**, in a separate sitting, and is the metric.
5. Commit it. An unrecorded run did not happen.

⚠️ **Step 3 is not fussiness — it is the one thing that can void the measurement
rather than inform it.** `repo_root()` fails soft: in a directory that is neither
a git repo nor a socom root it returns the current directory and plants ~33 files
there. The operator did exactly this on 2026-08-05, on their own machine, inside
two minutes, following `PILOT.md` verbatim — cloned into a subdirectory, ran
`quickstart` from the parent, and adopted a scratch folder. **They read the
result as socom repeating itself rather than as a wrong-directory adopt**, and
nothing in 110 lines of output says which directory is being adopted except one
word on line 3. A participant who does this spends the whole session measuring a
folder, and the run tells you nothing about socom.

The defect ([[DEF-QUICKSTART-REPORTS-ADOPTION-IN-NON-GIT-REPO-01]]) is **not**
repaired, deliberately — see `decisions/0004`. It is mitigated here instead,
because the observer is present and one line of protocol costs nothing and
deletes no finding, where a code repair would touch the metric surfaces §4 exists
to test.

**The sheet is the observer's, not the participant's.** Handing it over turns an
observation into a survey and deletes (a) — a participant who knows a "stall
point" field exists narrates their stalls instead of having them.

## The four prohibitions

Each is in the row for a reason, and the run is void if one is broken:

- **No demo.** A walked-through session measures the author's explanation.
- **No favours.** Politeness produces a first use and never a second — which is
  precisely the signal being read.
- **No doc fixes first.** Where `PILOT.md` confuses a stranger IS the finding.
- **No agent substitute.** A cohort ran 2026-08-03 and produced none of this
  row's output: zero stall points (agents do not quit — one installed a Go
  toolchain rather than stop), zero unstaged value (3/5 planted the defect they
  then caught), and nobody reached run #2. **An agent cohort can falsify and
  cannot confirm.**

## A result of "stopped at step 2, never ran it again" is COMPLETE

It is not a failed session and it is not a reason to run a sixth. It is the kill
signal the solo Phase 3a trial structurally cannot produce, and recording it
closes the row exactly as a positive result would.

## Known defects that do NOT fire at n=1

Do not repair these first; neither can reach a single-session participant.

- [[DEF-UNRESOLVABLE-GATE-LEAVES-NO-TRACE-01]] — needs the downloaded file to be
  moved or cleaned *after* install. Takes days.
- [[DEF-BLACKBOARD-GRANTS-ON-UNREACHABLE-REMOTE-01]] — needs two concurrent
  sessions.

The four `READY P1` rows in `buckets/defects.md` are likewise deliberately
unrepaired. `DEF-STATUS-CLAIMS-UNLABELLED-01` most of all: `PILOT.md` asks *"did
a metric mislead you?"*, so repairing it first deletes a finding the participant
is meant to generate.

## Preflight (re-run before each session — it is 30 seconds)

A broken first touch burns a scarce participant on nothing.

```sh
curl -fsSL -o /tmp/socom.pre \
  https://raw.githubusercontent.com/Morse2580/socom/main/bin/socom \
  -w 'http=%{http_code} bytes=%{size_download}\n'
chmod +x /tmp/socom.pre && /tmp/socom.pre --help | head -3 && /tmp/socom.pre version
```

Expect `http=200`, a non-trivial byte count, and the command list. Last verified
2026-08-11 against `55d1397` — **200, 436923 bytes**, byte-identical to
`bin/socom` (`cmp`), build **`77425a0cead4`**.
⚠️ This number was **three builds stale** here on 2026-08-11 (it still read
`430621` / `a1cf0802daef` from 2026-08-06, across the `f1dce80` install repair
and the `0008` quickstart repair). That is Regression Test 1 recurring in the one
file a participant is told to trust, which is why the warning below exists.

⚠️ **Record the `version` build digest on the sheet** — it is the build-under-test
row, and a result that cannot name its build is not reproducible evidence. The
byte count changes on **any** merge touching `bin/socom`; re-run rather than
trust the number above.

⚠️ **This note is now history, kept so the change is not mistaken for a
regression.** `--help` used to write to **stderr** and exit **1**, so `| head -3`
did not truncate it and the whole command list scrolled past. It was recorded
here as cosmetic and deliberately **not filed** (the bucket has a stated
no-growth norm). It changed anyway on 2026-08-06 as scope of
`DEF-SUBCOMMAND-HELP-MUTATES-STATE-01`, whose repair would otherwise have left
socom answering `--help` two different ways: it now prints to **stdout** and
exits **0**, so `| head -3` truncates as written. Bare `socom` with no command
still exits 1 on stderr — that is a usage error, not a request to explain.

**Also confirm the participant is on macOS / Linux / WSL.** Native Windows is
unsupported (`fcntl` — the tool exits loudly), and discovering that during the
session wastes the run.
