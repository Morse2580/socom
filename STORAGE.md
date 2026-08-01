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

## The blackboard store (findings + path leases)

A second store, deliberately dumber than the index above: no chunking, no
embedding, no ranking. A finding is *authored*, not inferred, and it is
delivered by exact artifact match. Nothing here has to be right about
relevance — only about delivery.

```
.socom/blackboard/findings/<author>.jsonl     append-only
.socom/blackboard/leases/<author>.jsonl       append-only
```

**One shard per author is the whole concurrency design.** No session ever
writes another's file, so the union of shards is always well-defined and there
is no merge strategy to get wrong. Records are never mutated; state changes are
new records that reference an earlier `id`.

| kind | fields |
|---|---|
| `finding` | `id ts author artifact claim evidence status tier` |
| `resolve` | `id ts author ref verdict note` — closes the finding at `ref` |
| `lease` | `id ts author paths[] intent ttl_s` |
| `release` | `id ts author ref` — retires the lease at `ref` |

`tier` is `verified` when evidence was supplied, else `asserted` — derived from
the record, never self-declared, because an agent grading its own claim is the
self-assessment that degrades behaviour (arXiv 2310.01798, ICLR 2024). Real
certification is a later increment and must come from **repo outcome** (CI
passed, commit reverted, defect recurred) — a non-LLM signal.

`verdict` is `fixed | retracted | superseded`. **`retracted` means the claim
was never true**, and it is the reason `resolve` carries a verdict at all —
see RESIDUALITY §R2.

Every free-text field is control-char-stripped and length-capped **on write**,
so a poisoned record never enters the store. See PROTOCOL §7.1.

### Sync: a git ref, pushed directly

```
attest / claim / resolve  → append to this author's shard
                          → git push origin <commit>:refs/socom/blackboard
claim                     → git fetch, union every shard, filter by artifact
```

The commit is built with plumbing against a throwaway `GIT_INDEX_FILE`, so the
session's real index and working tree are never touched. Not a branch and not a
commit on the working branch: **a finding that arrives when an MR merges cannot
change what an agent did at claim time.** Measured cost: 263 bytes per finding
record; `refs/socom/*` is not fetched by a default clone, so it never bloats a
checkout that does not use it.

### Projection out (the graph seam)

The same property that makes the index projectable applies here, and it is the
reason git is not a one-way door: append-only records with stable ids and typed
fields load into any store — graph, SQLite, DuckDB — with a small importer that
never parses anything but JSONL.

```
projector (any impl) → reads findings/*.jsonl + leases/*.jsonl,
                       upserts by record id (ids are content-derived and stable),
                       folds resolve/release the same way bb_open_findings does
```

Git's real ceiling is not size, it is **query**: "which findings about auth were
retracted by someone other than their author last month" requires reading
everything. That wall arrives long before the storage wall, and it is the
signal that a projection is now earned. Until findings are demonstrably worth
acting on (see PILOT §the tally), a richer store would be indexing records
nobody used.

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
