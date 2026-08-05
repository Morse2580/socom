# 0005 — The user is an agent; the adopter is not

**Status:** **PROPOSED 2026-08-05 — not accepted.** Amending `0001` is reserved to
the operator; this document argues the question and recommends a verdict, and one
line flips it.
**Supersedes:** nothing. **Resolves:** whether `EV-NONAUTHOR-EXPOSURE-01` names
the wrong population — whether socom's user is an *agent*, in which case a
non-author *human engineer* is the wrong instrument and the row should be
amended or retired.
**Upstream:** `0001` §Decision, and the §10 ROOT GATE of 2026-08-01.

---

## The question, as put

> *"Do we actually need to wait for the exposure? I can test every single
> assumption — I can take charge as the actual verifier agent."*

The self-verification half is answered by the row's own scope and needs no
document: `bench/exposure/README.md` measures **voluntary second use by a
non-author** and states that it does **not** measure whether socom is well-built.
The author can settle the second and not the first.

The half that deserves a decision is the one underneath it: **if socom's user is
an agent, a human engineer is the wrong population**, and the row is
mis-specified rather than merely unrun. That is a real argument with real
evidence, and it is the only legitimate route to "the exposure is not needed."

---

## What the amendment gets right — conceded in full

socom's **user** is an agent. This is not arguable, and every artifact it
generates says so:

| Evidence | Where |
|---|---|
| Every compiled adapter targets an agent runtime | `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/socom.mdc`, 7 × `.claude/agents/*.md` |
| The blackboard's stated users are agents | `blackboard.py:20` — *"Agents do not message each other… A bulletin reaches the agent who starts tomorrow."* |
| An MCP server exists solely to serve them | `mcp.py` — `claim`, `attest`, `findings`, `resolve`, `release` over stdio |
| `PILOT.md`'s own guided path is an agent path | *"SOCOM is built for Claude Code"* |
| R1's subject matter is agent instruction files | drift between `CLAUDE.md`/`AGENTS.md` and the repo |
| The field pain the scouts found is agent-shaped | `anthropics/claude-code#15443`, `#37888`, Cursor forum — agents ignoring rules that are still correct |

Anyone arguing socom is a tool humans operate directly is wrong. The verbs are
run by agents, the documents are read by agents, and the seams are agent seams.

---

## What it does not reach: the user is not the adopter

The root gate did not name usage. It named **adoption**:

> The load-bearing mechanism is not an engine, a schema, or a protocol. It is
> **adoption by someone who is not the author**. That mechanism has never been
> executed. Six public artifacts, five months, zero users.

Adoption is a **decision**, and the two roles come apart cleanly:

| | Who | What they do | Can they produce the D0→D1 signal? |
|---|---|---|---|
| **User** | an agent | runs `claim`, reads `CLAUDE.md`, trips a gate | **No** — see below |
| **Adopter** | a human | decides socom is planted, that `core.hooksPath` is rewritten, and that it is **still there next week** | **Yes** — this is the only party that can |

**An agent cannot generate the metric, structurally.** The metric is *voluntary
second use* — `0001`: *"did they run it again when nobody was watching. Binary,
cheap, unfakeable. First use is compliance; second use is value."* If
`CLAUDE.md` says `socom claim`, the agent runs `socom claim`. That is compliance
**by construction**, and compliance is precisely the half the metric discards. An
agent has no state in which it declines to use a tool its instructions name — so
it cannot supply the signal, no matter how many run.

### This is measured, not theorised

Two agent cohorts have already run against socom, and both are recorded:

| Cohort | Date | Output | Effect on the proof tier |
|---|---|---|---|
| Cold-run, 5 agents, 5 real repos | 2026-08-03 | ~30 defects, 4 P0 | **none** |
| 5-substrate breakage sweep, 5 agents | 2026-08-05 | 3 P0, 20+ subcommands, zero crashes | **none** |

`bench/exposure/README.md` records why, and the reason is the argument in
miniature: *"zero stall points (agents do not quit — one installed a Go toolchain
rather than stop), zero unstaged value (3/5 planted the defect they then caught),
and nobody reached run #2. **An agent cohort can falsify and cannot confirm.**"*

Ten agents produced seven P0 rows and moved D0 by nothing. That is not a shortage
of agents. It is the wrong instrument for the claim, run twice.

### The thesis is about humans

`PILOT.md` states the claim socom exists to test: *"five senior engineers can
plausibly oversee thirty."* The engineers are the subject; the thirty are the
agents. A thesis about whether **humans** can oversee agent fleets cannot be
cleared by measuring agents. The population in the row is the population in the
thesis.

---

## What WOULD be a legitimate new instrument

The amendment fails as a replacement for the exposure and succeeds as an argument
for something socom does not currently have: **an agent-behaviour A/B**.

> Same repo, same task, same model, one variable: socom present or absent. Does
> the agent's compliance with the repo's own declared rules measurably change?

That is real, it is author-runnable, it needs no recruit, and nothing in `0001`
forbids it — the R1 acceptance corpus is already precedent for an instrument in
the *"Needs people? **no**"* column, and it is `DONE`. It would establish
**efficacy**: does socom change what an agent does.

⚠️ **It is a supporting instrument, not a blocking one.** It cannot clear D0, for
exactly the reason `0001` §Decision(3) demoted the blackboard: *"It cannot clear
D0 no matter what it reads, because it is not measuring the blocking claim."*
Efficacy is not adoption. A tool can change agent behaviour measurably and still
be a tool nobody chooses to keep — and "nobody has chosen to keep it" is the
entire content of D0.

⚠️ **And it carries the classic trap.** Building an A/B harness is capability,
`0001` blocks capability, and an instrument that must be *built* before it can
measure is the shape of every one of the seven prior attempts. If it is run at
all, it is run by hand, on one repo, with two transcripts and a diff — not as a
new subsystem.

---

## Recommendation

**Refuse the amendment. The row stands as written, unamended.**

The refusal rests on the amendment's own distinction, not against it: socom's
user is an agent, socom's adopter is a human, and *voluntary second use* is a
property only an adopter has. Ten agents across two cohorts have already
demonstrated the gap empirically rather than by argument.

Three things follow:

1. `EV-NONAUTHOR-EXPOSURE-01` is unchanged and remains the only row that can move
   the proof tier.
2. **The agent-behaviour A/B is recorded here as a legitimate instrument** and may
   be run by hand at any time, before or after the exposure. It does not compete
   with the exposure and does not clear D0. If it is ever built rather than run,
   that is capability and `0001` blocks it.
3. The author-runnable lane is **not empty and never was** — the R1 acceptance
   corpus is `DONE`, and the 2026-08-05 field run produced eleven findings and
   `0004`. What that lane cannot produce is a second use by someone who did not
   build it.

---

## The asymmetry, stated once

Running the exposure unnecessarily costs one engineer, one hour, and one
follow-up question a week later. Skipping it on the strength of author
verification means shipping something no one but the author has ever used — and
the single judgement never tested across five months, seven public artifacts and
D0 is the author's judgement about whether anyone would use it.

---

## Trigger that reopens this

- A **non-author adopter who is not a human** — an agent that installs socom into
  a repo on its own initiative and keeps it. That is not currently a thing that
  happens, and if it becomes one, the population genuinely has changed and this
  document is wrong.
- The exposure returning a result whose stall point is **agent-side** — the
  participant stops because their *agent* did something socom caused. That would
  show the two roles are less separable in practice than they are on paper.

---

## Provenance

Nothing here is new measurement. It reasons over the root gate of 2026-08-01
(quoted via `0001` §Context), `0001` §Decision and §What measuring should be,
`bench/exposure/README.md` §What this measures, `PILOT.md` §the blackboard trial,
and the two recorded agent cohorts of 2026-08-03 and 2026-08-05. Code references
re-grepped at `42bc073`. **HYPOTHESIS, marked as such:** the claim that an agent
cannot decline a tool its instructions name is an argument from the construction
of agent runtimes, not a measurement — the agent-behaviour A/B above would test
it, and if agents are observed declining socom while instructed to use it, this
document's central distinction weakens.
