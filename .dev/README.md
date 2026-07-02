# .dev — strategy & design docs

Non-shipping documents: the *why* and the *where-next*, kept out of the repo root
so the root shows only what the tool **is** (`bin/`, `src/`, `canon/`, `schemas/`,
`adapters/`, `templates/`, `tests/`, `bench/`, `build.py`, `socom.yaml`). None of
these are read by the tool at runtime; they are for humans reasoning about it.

| Doc | What it is |
|---|---|
| [`VISION.md`](VISION.md) | The end goal — widen the fraction of work that runs unsupervised without losing coherence. |
| [`ROADMAP.md`](ROADMAP.md) | The sequence: Safe → Measurable → Proven → Wider → Scaled. Phase status lives here. |
| [`GAPS.md`](GAPS.md) | Gap analysis vs. the field, anchored to the vision. |
| [`PROTOCOL.md`](PROTOCOL.md) | The full substrate specification. |
| [`PILOT.md`](PILOT.md) | The 5-minute pilot / discovery path (what's safe to test in v0.1). |
| [`RESIDUALITY.md`](RESIDUALITY.md) | Residuality stress pass 1 — the naive design. |
| [`RESIDUALITY-2.md`](RESIDUALITY-2.md) | Residuality stress pass 2 — the hardened design. |
| [`STORAGE.md`](STORAGE.md) | Storage & identity model (chunk ids, ledger, run records). |

The shipped entry doc stays at the root: [`../README.md`](../README.md).
