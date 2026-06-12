# SOCOM Vision — the transformational arc

Status: capture draft, 2026-06-12. Companion to `PROTOCOL.md` (the spec);
this is *why* and *where it goes*.

---

## 1. The durable-foundation principle

The substrate's knowledge lives in **natural language** — principles,
memories, lessons, decoded operator feedback — because natural language is
the one representation that *appreciates* as models improve. Deterministic
code rots with platforms; prompts and prose get more leverage with every
model generation.

But natural language alone drifts. So every artifact is **contracted against
XML**: a schema'd envelope that makes it addressable, assessable, indexable,
and enforceable. The prose is the payload; the XML is the promise.

> In-context learning with a durable foundation: the substrate is
> ever-evolving, learning from each opportunity in natural language that
> survives model upgrades — contracted against XML so it never degrades into
> vibes.

This is also the obsolescence hedge: when a stronger model arrives, the same
substrate produces better output with zero migration. Participants are
disposable; the protocol compounds.

## 2. Who it transforms

The substrate is not just for coders. Its seats are defined by substrate
operations, so non-coding work plugs in identically:

**Domain architects.** "Not sure I'll have a lot of code work in the near
future — but I can see how it helps me with generating ADRs / documentation."
The substrate already treats ADRs, runbooks, and contracts as first-class
promised artifacts with gates (claim-verification, review seats). An
architect's session produces ratified decisions and documentation through the
same loop a builder uses for code — research-first, contract-first,
verified-never-claimed.

**Data engineers.** The substrate *is* the engineering philosophy the
platforms themselves follow — and that symmetry is the point:

- *Treat data like code* → here, treat **engineering work itself** like a
  data product: versioned, contracted, quality-gated, golden-pathed.
- *Data primitives / quanta* → the promise is the smallest autonomous unit of
  work; aggregated initiatives compose promises the way a customer-360
  composes source-aligned products.
- *Shift-left quality* → gates fire at task-completion and pre-commit, not at
  review time. Stop the pollution at the source, don't clean the river
  downstream.
- *Breaking-changes problem* → the use-promise (−): downstream participants
  rely only on contracted ports; a column change that breaks consumers is a
  broken promise with named assessors and a deprecation protocol — not a
  6-months-ignored agreement.

**Developers generally.** Faster *because of* the principles, not despite
them: the room is pre-loaded (retrieval map), done-ness is pre-agreed
(contract), verification is mechanical (gates), and nothing is re-derived
(escalation ladder turns every repetition into infrastructure).

**Data analysts (extension target, not v1).** A place to explore data faster
than ever: the same contracts that govern products describe their semantics
(ubiquitous language, classifications, business keys), so an analyst seat can
query *through* the substrate with trustworthy metadata. Pointing AI at data
without metadata yields unreliable inference; pointing it at
contract-described data yields grounded answers. v1 must merely not preclude
this; the artifact schemas already carry what it needs.

## 3. Governance: promises, not permission

From Promise Theory as applied to data governance (Paul / Gaming One
conversation, 2026-06):

- **Contracts are agreements; promises are autonomous commitments backed by
  code.** Owners declare what they will deliver; the platform enforces it
  automatically.
- **Don't tell the teenager to clean their room.** Governance that depends on
  telling people what to do does not govern. Rules are code-enforced with
  **staged severity: amber (warning, deadline attached) → red (breach,
  blocked)**.
- **Remove people from approval bottlenecks.** "Computer says no" is the
  enforcement mechanism; humans spend judgment on architecture and product
  decisions, not on gatekeeping that a gate can do.

SOCOM gates therefore support staged enforcement: a gate may declare an amber
band (warn + record + deadline) before its red band (block). Trust per seat
(kept-promise history) widens or narrows the amber band — high-trust seats
get longer leashes, broken promises tighten them. Approval latency goes to
zero while standards go *up*.

## 4. The evolution ladder

Each level is additive — the substrate never depends on the level above it,
and degrades gracefully to the level below.

**L0 — Files + index (the floor, always works).** Plain artifacts in git,
deterministic retrieval via the lifecycle index and domain sharding. Greppable
by any participant including humans. This level alone already beats most
agent setups.

**L1 — Naive RAG.** `socom index` walks the registry: element boundaries are
chunk boundaries, attributes are filters, `embed="true"` marks payloads. One
indexer, zero artifact-specific code, any vector store. Associative recall
("what does the substrate know about Livy retries?") complements the
deterministic map.

**L2 — Advanced RAG.** The schemas make the classic upgrades cheap because
structure already exists: hybrid retrieval (attribute filters + vectors),
the `[[link]]` graph as a re-ranking signal, lifecycle/recency weighting,
supersession-aware retrieval (never surface a superseded rule without its
successor), promise-state filtering (open blockers rank above kept history).

**L3 — Agentic RAG.** Retrieval itself becomes a seat: a librarian role that
*promises* decision-ready context — decomposing the question, walking the
link graph, assessing freshness against origin, and returning a briefed
bundle with provenance. The retrieval map (when) + role triggers (who) +
artifact registry (what) already encode its dispatch rules; L3 makes the
lookup itself accountable to a contract.

**L4 — Containerized substrate.** The room becomes literal: `socom up` gives
any developer on any repo a sealed container — worktree, compiled runtime
adapters, hydrated memory, gates wired, retrieval service running, egress
scoped to the contract. The substrate ships as an image; an org runs a fleet
of rooms the way it runs CI. This is the "across all repos, all developers"
deployment story: substrate-as-a-service, with the org constitution layered
under each repo's bindings.

## 5. The flywheel

1. Every session leaves artifacts (handoffs, memories, lessons, kept/broken
   promises).
2. The escalation ladder converts repetition into infrastructure (memory →
   lesson → procedure → workflow → gate → ADR).
3. Retrieval makes the accumulated substrate cheap to wield (L1→L3).
4. Trust scores reallocate autonomy toward seats that keep promises.
5. Output is *more* automatable than its inputs — contracts force coverage,
   procedures enforce structure — so each cycle widens what can run
   unsupervised.

Team capacity, not individual productivity, is the unit: supervision
concentrates on genuine judgment, execution runs against the protocol.

## 6. Non-goals (v1)

- Analyst-facing data exploration UX (extension target; schemas must not
  preclude it — see §2).
- Org-wide memory federation precedence rules (open question in PROTOCOL §15).
- Any dependence on a specific vendor, model, or runtime — by definition.
