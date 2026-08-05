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
3. §5 is filled **one week later**, in a separate sitting, and is the metric.
4. Commit it. An unrecorded run did not happen.

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
chmod +x /tmp/socom.pre && /tmp/socom.pre --help | head -3
```

Expect `http=200`, a non-trivial byte count, and the command list. Last verified
2026-08-05 against `d23fa0c` — 200, 408964 bytes, identical to `bin/socom`.

**Also confirm the participant is on macOS / Linux / WSL.** Native Windows is
unsupported (`fcntl` — the tool exits loudly), and discovering that during the
session wastes the run.
