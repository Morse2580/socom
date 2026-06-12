# SOCOM Storage Mapping — files → database, flawlessly

The substrate's L0 form is files in git, and that never changes: git remains
the write path and the source of truth (substrate invariant §2, residue R6).
A database — relational, document, or vector — is always a **projection**,
rebuilt from the registry, never an authoring store. This is the same rule
the data platforms downstream of this substrate live by.

This document is the contract that makes the projection mechanical: when the
time comes to put the registry in a database, nothing about the artifacts
needs to change — the schema below falls out of what `socom index` already
emits.

## Identity (the part that must be flawless)

Every chunk has a **stable, deterministic identity**, assigned at index time
and reproducible from the artifact alone:

```
artifact_id = <path relative to repo root>            e.g. .socom/canon/constitution.xml
chunk_id    = <artifact_id>#<element-path>[.<id-attr>] e.g. ...#principle.verify-never-claim/md
content_sha = sha256(normalized chunk text)[:16]
```

Rules that make re-projection safe:

1. **`chunk_id` is positional + declared** — derived from the element path
   and `id` attributes, never from content. Editing a chunk's text keeps its
   identity (it's the same rule, reworded); `content_sha` changes, which is
   exactly the signal an upsert needs.
2. **`content_sha` drives change detection** — a projection sync is
   `upsert where content_sha differs; delete where chunk_id vanished`.
   Idempotent, repeatable, no diffing of prose.
3. **Lifecycle travels as data** — `state` (active/superseded/retired/open/
   kept/broken) is a filter column, so a vector query can exclude retired
   rules *in the WHERE clause*, not in post-processing. Superseded artifacts
   keep their rows (history is queryable) but carry `superseded_by`.
4. **Embedding versions are explicit** — `embedding(model, dims, vector)`
   is a separate table keyed by `(chunk_id, model)`: re-embedding with a new
   model is an additive migration, never an overwrite, and A/B-ing two
   embedding models is a join, not a re-index.

## Relational projection (reference DDL)

```sql
CREATE TABLE artifact (
  artifact_id   TEXT PRIMARY KEY,     -- repo-relative path
  artifact_type TEXT NOT NULL,        -- promise|memory|lesson|handoff|role|gate|decision|runbook|doctrine
  socom_version TEXT NOT NULL,
  state         TEXT,                 -- lifecycle
  domain        TEXT,
  session_id    TEXT,
  superseded_by TEXT REFERENCES artifact(artifact_id),
  raw_xml       TEXT NOT NULL,        -- full round-trip fidelity
  indexed_at    TIMESTAMPTZ NOT NULL
);

CREATE TABLE chunk (
  chunk_id     TEXT PRIMARY KEY,
  artifact_id  TEXT NOT NULL REFERENCES artifact(artifact_id) ON DELETE CASCADE,
  element      TEXT NOT NULL,         -- verbatim|decoded-rule|why|goal|md|...
  text         TEXT NOT NULL,
  content_sha  TEXT NOT NULL,
  metadata     JSONB NOT NULL DEFAULT '{}'  -- flattened element+artifact attrs
);

CREATE TABLE embedding (
  chunk_id   TEXT NOT NULL REFERENCES chunk(chunk_id) ON DELETE CASCADE,
  model      TEXT NOT NULL,
  dims       INT  NOT NULL,
  vector     VECTOR,                  -- pgvector; or external store keyed the same
  PRIMARY KEY (chunk_id, model)
);

-- The retrieval question the substrate actually asks:
--   "active artifacts of these types, in this domain/lifecycle, nearest to q"
CREATE INDEX chunk_meta ON chunk USING GIN (metadata);
CREATE INDEX artifact_filter ON artifact (artifact_type, state, domain);
```

The same shape maps 1:1 to any document store (artifact = document, chunks =
sub-documents) or dedicated vector DB (chunk_id = point id, metadata =
payload). Nothing in the substrate names a vendor.

## Sync protocol

```
socom index           → .socom/index/chunks.jsonl   (already exists; L0/L1 boundary)
projector (any impl)  → reads chunks.jsonl, upserts by chunk_id where
                        content_sha differs, deletes vanished chunk_ids,
                        embeds new/changed chunks per model row
```

The projector can be a 50-line script, a dbt model, or a Fabric notebook —
it consumes JSONL with stable IDs and never parses XML itself. Redaction
(HR6) happened upstream at index time, so the projection is safe by
construction.

## The baseline gate (when RAG is allowed to start)

Naive RAG starts **only after an L0 performance baseline exists** — otherwise
"the vector store made retrieval better" is a claim, not a verified result
(constitution §verify-never-claim applied to the substrate itself).

`socom baseline` measures and records, in `.socom/index/baseline.json`:

- corpus shape: artifacts, chunks, tokens-ish size, per-type counts
- L0 latency: cold grep across the registry, index walk time
- retrieval probes: a configurable set of `query → expected chunk_id`
  pairs (`.socom/index/probes.yaml`), scored by hit@k under L0 (substring/
  keyword match) — the floor any L1 implementation must beat

L1 acceptance contract (amended per R10, recorded in `probes.yaml`): ≥12
probes, hit@5 ≥ L0 AND MRR@5 strictly greater, latency within budget, zero
redaction violations. The contract was written *before* the ranker was chosen
— contracts before code, applied to the substrate's own evolution — and
`socom eval` enforces it as a red gate: an L1 that doesn't beat the floor may
not serve.

**L1 status: implemented and accepted** (2026-06-12). Ranker: BM25 over the
post-redaction registry — pure stdlib, offline, deterministic; no vendor, no
keys. `socom embed` builds `.socom/index/vectors.json`; `socom query`
serves L1 with a loud L0 degrade when the index is absent (R6), filters
retired/superseded/broken artifacts (lifecycle-aware), and prints provenance
per hit. First acceptance run: L1 14/16 hit@5, 0.7812 MRR@5 vs L0 13/16,
0.6687 — accepted. The two recorded misses are paraphrase gaps; closing them
is L2's job (semantic embeddings as a *pluggable upgrade* into the same
`embedding(chunk_id, model)` slot above — never a dependency).
