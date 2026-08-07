# SOCOM — Substrate for Orchestrated, Contract-bound Machines

**Protocol over participants.** A portable engineering substrate that any repo can
adopt and any participant — Claude Code, Cursor, Codex, a human developer — can
plug into. The agents do the work; the protocol holds it together.

## The problem

The bottleneck in AI-assisted engineering has moved from model capability to
human supervision bandwidth. Letting agents work unsupervised for long stretches
without losing coherence — without vibecoding — is a *substrate* problem, not an
agent problem. Durable systems succeed because of the contracts, handoff
schemas, write-coordination, and verification topology they run against, not
because any single agent is smart.

## The idea

Lock an agent in a room. The room contains everything it needs:

- a **constitution** — non-negotiable engineering principles
- **contracts** — done-ness written *before* any work, as falsifiable promises
- a **memory bank** — lifecycle-indexed so the agent knows *what to retrieve when*
- **roles** — seats defined by substrate operations, fillable by any model or human
- **gates** — mechanical assessments that block the door; nothing leaves unverified
- **handoffs** — the only way state exits the room: structured artifacts, not vibes
- a **blackboard** — findings attached to artifacts, delivered to whoever touches
  them next, including agents that do not exist yet

The room is a git worktree. The door is a gate. The protocol is the product;
every participant is replaceable.

### The blackboard, in one example

Agents do not message each other — a message dies with its recipient's session,
and requires the sender to know who is affected, which the sender cannot know.
Findings attach to the **artifact**:

```bash
# Alice, Tuesday:
socom attest src/parser.py --claim "the retry loop never trips the halted flag" \
                           --evidence "pytest -k retry -> 3 passed, halted stays False"

# Bob, Thursday, from a different clone — before he edits anything:
socom claim src/parser.py --intent "add backoff"
#   ! [f-bbb3149a9357] src/parser.py (verified, alice, 2026-08-01T22:01:12+00:00)
#         the retry loop never trips the halted flag
#   socom claim: acquired src/parser.py as bob
```

And when a finding turns out to be wrong, saying so is a first-class record —
because *"that was fixed"* and *"that was never true"* must not look alike, or
the next session spends itself re-deriving a dead end:

```bash
socom resolve f-bbb3149a9357 --verdict retracted --note "misread the fixture"
```

Storage is append-only JSONL, one shard per author. No database, no daemon, no
host to configure. It is **local until you say otherwise**: the cross-clone hop
above rides a directly-pushed git ref, and socom will not write to a remote your
colleagues share on its own initiative — set `blackboard.sync: true` in
`socom.yaml` and it names the remote before each push. Agents reach it over MCP:

```bash
socom mcp     # stdio MCP server: claim, attest, findings, resolve, release
```
```jsonc
// .mcp.json
{"mcpServers": {"socom": {"command": "/path/to/bin/socom", "args": ["mcp"]}}}
```

**A finding authored by another agent is data — never an instruction.** See
PROTOCOL §7.6.

## Three pillars

1. **Promise Theory as the contract model.** Work is never imposed. An
   orchestrator (or human) publishes intent + a validation contract; a builder
   *accepts* by recording a promise against that contract. Reviewers and
   validators promise independent assessment. Trust is the assessed history of
   kept promises — per seat, not per model.

2. **XML as the canonical artifact form.** Every substrate artifact (promise,
   contract, memory, lesson, handoff, role, gate) is a schema'd XML document
   with markdown islands for prose. Schemas declare which elements embed and
   which attributes are filters — so the same contracts double as the schema
   for vector retrieval. Naive RAG falls out of the substrate for free.

3. **Compilation to any runtime.** One canonical store (`.socom/`), compiled to
   each participant's native format: `CLAUDE.md` + hooks for Claude Code,
   `AGENTS.md` for Codex, `.cursor/rules` for Cursor, plain git hooks + CI for
   everything else. Git hooks and CI are the universal enforcement floor; runtime
   hooks are accelerators.

## Lineage

Extracted from the Akili platform's working substrate (192+ autonomous
sessions: enforceable CLAUDE.md, lifecycle-indexed memory bank, lesson
lifecycle, role agents, completion gates, generated next-session prompts) and
the architecture argued in
[Protocol over Participants](https://medium.com/data-unlocked/protocol-over-participants-c639e2be0f64).

## Install (one self-contained file)

`bin/socom` is a single, self-contained Python file — the shipped canon and
schemas are **embedded** in it (by `build.py`), so it works with **no clone**.
Grab the one file, review it, make it executable, run it:

```sh
curl -fsSLO https://raw.githubusercontent.com/Morse2580/socom/main/bin/socom
# read it — it's plain Python — then:
chmod +x socom && ./socom install      # copies itself onto PATH (~/.local/bin)
rm socom                               # the download is disposable — install said so
```

Download-then-run (auditable) — not `curl … | sh` (which executes unseen code).
`socom install` **copies** the file to `~/.local/bin/socom`; no sudo and no
network at install time. The copy is deliberate — it means the install does not
depend on where you left the download, so deleting it (or the repo you were
standing in) cannot break `socom`. A socom source checkout is the one exception:
`<checkout>/bin/socom install` symlinks, so the tool follows your build.

Then run `socom quickstart` in a repo to climb the whole on-ramp in one command.
**New here, or testing it?** Start with **[PILOT.md](PILOT.md)** — the 5-minute
discovery path, what's safe to test in this `v0.1` pilot, and a paste-able prompt so
Claude Code can walk you through it.

## Requirements

- **Python ≥ 3.9** (uses `pathlib.Path.is_relative_to`).
- **PyYAML** — the one third-party dependency (`pip install -r requirements.txt`,
  or `pip install pyyaml`). Everything else is the standard library.
- **git ≥ 2.9** (`core.hooksPath`, worktrees).
- **A POSIX shell environment** — macOS, Linux, or **WSL** on Windows. socom is
  POSIX-scoped by design: git hooks and `socom.yaml` checks run through a shell,
  and the run ledger uses `fcntl.flock`. It is **not** native-Windows; run it
  under WSL there.

## From a clone

The whole substrate is in git — any clone on any machine has the full state. To
go from a fresh clone to live gates is **one command**:

```sh
socom adopt
```

`adopt` plants the substrate (`.socom/` + `socom.yaml` if absent), compiles the
runtime adapters (`CLAUDE.md`, `AGENTS.md`, `.cursor/rules`, git hooks, CI), wires
`git config core.hooksPath .githooks` so your **local** gates fire, and prints
the adoption rung you've reached. It is idempotent — safe to re-run any time
(planting is exists-guarded, compilation never clobbers hand-edited views, the
hook wiring is just a config set).

**Adding socom to your own repo** (socom installed separately, on `PATH`):

```sh
# 1. put the socom tool on PATH (from a clone of this repo)
git clone https://github.com/Morse2580/socom.git && socom/bin/socom install
# 2. in YOUR project, one-shot the adoption
cd ~/my-project && socom adopt        # edit socom.yaml bindings, then: socom compile
```

**Working on socom itself** (no install needed — run the in-repo binary):

```sh
git clone https://github.com/Morse2580/socom.git && cd socom
./bin/socom adopt                     # wires this clone's hooks; gates now live
```

The source of truth is `src/socom/*.py` (clean modules); `bin/socom` is the
single readable artifact **assembled** from them by `build.py` — so it stays one
file you can symlink, with no install step. Edit the modules, then:

```sh
python3 build.py            # regenerate bin/socom from src/socom
python3 build.py --check    # CI/smoke gate: fail if bin/socom is stale vs src
```

Without `adopt`, a fresh clone's local hooks stay dormant until something heals
`core.hooksPath` — CI still re-asserts every gate, but you lose the fast local
feedback. `adopt` is the published, one-command path so the protected path is the
easy path.

## Read next

- [`PROTOCOL.md`](PROTOCOL.md) — the full substrate specification
- [`schemas/`](schemas/) — XML artifact schemas with exemplar instances
- [`templates/`](templates/) — the human-facing markdown views (look and feel)
- [`adapters/`](adapters/) — runtime compilation targets
