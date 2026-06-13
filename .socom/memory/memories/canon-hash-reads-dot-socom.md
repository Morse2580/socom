---
name: canon-hash-reads-dot-socom
description: editing canon (gates/roles/etc) — which dir is authoritative, and the sync+compile step
metadata:
  type: reference
---

`canonical_hash()` in `bin/socom` reads from `<repo>/.socom/canon/`, **not** the
top-level `canon/`. The two are distinct:

- `canon/` — the **shipped template** `socom init` copies into a new repo's `.socom/canon/`.
- `.socom/canon/` — **this repo's live canon**; it drives the source hash and all compiled views.

**How to apply:** when changing a canon file (e.g. adding a gate to `gates.xml`),
edit **both** `canon/<file>` (so adopters get it) and `.socom/canon/<file>` (so this
repo uses it — keep them byte-identical), then run `socom compile`. Editing only
`canon/` does nothing to this repo; editing only `.socom/canon/` silently diverges
from the shipped template (`socom doctor` flags it as HR9 divergence). After compile,
`socom doctor` must be clean and the new source hash propagates to CLAUDE.md / AGENTS.md
/ .cursor / .githooks / CI adapters — commit all of them together or you get drift.

Discovered the hard way during the evals extraction (commit c405560): a gate added
to `canon/gates.xml` alone never reached the compiled views.
