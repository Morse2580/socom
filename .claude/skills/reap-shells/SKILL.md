---
name: reap-shells
description: Find and safely terminate stale, orphaned, or corrupt background shells — runaway `gh run watch` pollers, `while true` loops, watchers that never self-clear, and processes squatting a port — without self-killing the shell running the teardown. Use when a session has accumulated background-task churn, when a loop will not stop, when a port is "address already in use", or at closeout to leave a clean process table. Triggers on "kill stale shells", "reap background processes", "stop the runaway loop", "what's holding this port", "exit 144 self-kill".
---

# Reap Shells — safe teardown of stale/corrupt background processes

**Ported from Akili** (`/root/Akili/.claude/skills/reap-shells/SKILL.md`). The
trap, the classification table and the by-exact-PID rule are Akili's and are
unchanged — they are properties of `pkill`, not of either repo. The socom-specific
part is §socom has its own reaper, which is the one place the general procedure
would do damage here.

## The one trap this skill exists to prevent

`pkill -f <pattern>` and `pgrep -fc <pattern>` match against **every process's
full command line — including the command you are running right now.** If the
pattern appears in your own invocation (it usually does, you just typed it), you
match yourself:

- `pkill -f "gh run watch"` → kills its own shell → **exit 144**, silent, looks
  like a random failure.
- A watcher whose early-exit test is `[ "$(pgrep -fc "X")" = 0 ]` can **never**
  reach 0 — it always counts itself, so it loops to timeout.

**Rule: terminate by exact PID or harness task-id. Pattern-match only with `$$`
excluded.**

## Procedure

### 1. Enumerate — with lineage and lifetime

```sh
ps -eo pid,ppid,etimes,stat,args \
  | grep -iE "gh run watch|while true|nohup|sleep [0-9]|socom " | grep -v grep
```

- `ppid` — who spawned it. **`PPID=1` = orphan reparented to init**; usually a
  `nohup`/`setsid` survivor doing its job, not corruption.
- `etimes` — seconds alive. A process that is only ever a few seconds old across
  repeated checks is **restarting**, i.e. a churning loop.

### 2. Map ports → PID (find the squatter)

```sh
ss -ltnp | grep -E ':<port>'
```

Highest-signal step for "the thing keeps dying": a self-healing loop that keeps
failing is usually losing a bind race to an orphan that already holds the port.
Kill the *orphan* or stop the *loop* — not both blindly.

### 3. Classify

| Signature | Meaning | Action |
|---|---|---|
| `PPID=1`, holds a port, stable `etimes` | orphaned server doing its job | keep if needed, else `kill <PID>` |
| real PPID, loop body, tiny/cycling `etimes` | churning/corrupt loop | stop it (step 4) |
| harness background shell (has a task-id) | `run_in_background` task | `TaskStop <task-id>` |
| poll-watcher matching its own pattern | will never self-clear | `kill <PID>` |
| **anything under `.socom/runs/`** | a socom-spawned worker | **step 5 — do not hand-kill** |

### 4. Terminate — the safe ways only

```sh
TaskStop <task-id>            # harness-tracked background shells
kill <PID>                    # OS-level orphans, by EXACT pid — never pkill -f
for p in $(pgrep -f "gh run watch"); do [ "$p" != "$$" ] && kill "$p"; done
```

Escalate to `kill -9 <PID>` only if SIGTERM leaves it after ~2s.

### 5. socom has its own reaper — use it before you use `kill`

Processes launched by `socom spawn --exec` are **owned by socom's orchestration
loop**, and `gate session-start` reaps them itself: `reap_orphans()` (expired
claims) and `reap_dead_runs()` (a worker that died or finished without a verdict)
both run there — R12, *reap, don't just report*.

```sh
./bin/socom gate session-start        # reaps orphans + dead runs, prints what it took
./bin/socom claim --scan              # what leases are live, and whose
```

Hand-killing a spawn'd worker leaves the run record behind and makes socom's own
tally wrong — which is a defect you then get to investigate. Reap through socom
first; use `kill` only for what socom does not own.

⚠️ Blackboard identity is derived from the **working tree**, not the pid — a
one-shot invocation is no longer a different author (`DEF-RELEASE-NEVER-RELEASES-01`).
So a stale lease will NOT clear just because you killed the process that took it.
Use `socom release` (it refuses loudly and names the holder if it is not yours).

### 6. Verify — prove it is clean

```sh
ss -ltnp | grep -E ':<port>'          # expect EMPTY
ps -eo pid,ppid,etimes,args | grep -iE "<pattern>" | grep -v grep
```

Re-run step 1. **Do not claim "clean" without showing the empty output** —
`verify-never-claim` is rank 1 of socom's own constitution and it applies to
process tables too.

## Notes

- `TaskList` does not list `run_in_background` bash shells; those are tracked by
  the task-ids returned when they start.
- A grep that "finds" a stale process may be matching **its own command line** —
  confirm with `ps -p <PID>` before acting on a pattern hit.
- Don't kill another session's work. Identify ownership via `/proc/<pid>/cwd`
  before killing anything outside `/root/socom`.
- This skill reaps *processes*, not state. Leave `.socom/`, temp clones under the
  scratchpad, and any throwaway repo you are mid-reproduction on.
