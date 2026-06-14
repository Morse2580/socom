---
name: gates-velocity-first
description: designing any SOCOM gate/check/pre-flight — the heal/warn/block posture that keeps velocity fast
metadata:
  type: reference
---

Operator constraint for the substrate: **information velocity must stay fast AND
highest quality — a gate must never disrupt flow.** This is a design rule for
every gate, check, and pre-flight in SOCOM, not a one-off.

**The posture (in priority order):**
1. **Auto-heal** what is safely fixable (mkdir a dir, set a git config) — fix it
   inline, don't stop for it.
2. **Warn (amber)** by default — record + surface + proceed.
3. **Block (red)** ONLY on the genuinely unrecoverable (a missing tool, a
   destroyed precondition with healing disabled).
4. Keep it **fast band** (hard latency budget; print elapsed ms to prove it).
5. **Advisory > mandatory**: prefer a command the operator runs over a hard
   blocking gate; allow local bypass and let CI re-assert (`--no-heal` is the CI
   assert posture).
6. Surface the **exact fix at the altitude where it's met** (the published-gate
   doctrine) so resolution is instant.

`socom precond` (commit ea71c32) is the reference implementation of this posture.
`socom doctor` / the gate bands (amber warns, red blocks) follow the same spirit.
When adding a new gate, default to heal/warn; justify any red. Mirrors the
operator-feedback memory in the user bank. Related: [[canon-hash-reads-dot-socom]].
