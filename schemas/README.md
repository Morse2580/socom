# SOCOM Artifact Schemas

Every substrate artifact is a canonical XML document. Markdown lives inside
`<md>` islands for prose. Three rules give us Promise Theory semantics and
free retrieval:

1. **Promise envelope.** Stateful artifacts (promises, contracts, handoffs)
   carry `promiser`, `promisee`, `assessors`, and `state`. A promise binds only
   its maker; assessors are named at creation; state transitions are append-only.

2. **Retrieval declarations.** `embed="true"` on an element marks its text
   content for vectorization. Element boundaries are chunk boundaries.
   Attributes (`type`, `lifecycle`, `domain`, `state`, `session`) are filter
   metadata. `socom index` walks any artifact and emits `(id, text, metadata)`
   tuples with zero artifact-specific code — the contract schema IS the RAG
   schema.

3. **Verbatim preservation.** Human words travel in `<verbatim>` elements,
   typos preserved, never embedded *after* smoothing — the verbatim itself is
   what embeds, the decode is separate and labeled.

Exemplar instances in this directory (the schema-by-example; XSDs come once
the shape settles):

- `promise.xml` — intent → accepted promise → assessment (human↔agent and agent↔agent)
- `memory.xml` — decoded operator feedback in the canonical voice
- `handoff.xml` — session exit state
- `role.xml` — a seat definition with dispatch triggers

Markdown views in `../templates/` are compiled from these — humans read
markdown, machines read XML, neither is hand-maintained twice.
