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

The room is a git worktree. The door is a gate. The protocol is the product;
every participant is replaceable.

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

Without `adopt`, a fresh clone's local hooks stay dormant until something heals
`core.hooksPath` — CI still re-asserts every gate, but you lose the fast local
feedback. `adopt` is the published, one-command path so the protected path is the
easy path.

## Read next

- [`PROTOCOL.md`](PROTOCOL.md) — the full substrate specification
- [`schemas/`](schemas/) — XML artifact schemas with exemplar instances
- [`templates/`](templates/) — the human-facing markdown views (look and feel)
- [`adapters/`](adapters/) — runtime compilation targets
