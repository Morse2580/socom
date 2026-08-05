# 0003 — No standard binds a fork; socom already ratified the one idea that survived

**Status:** Accepted 2026-08-05
**Supersedes:** nothing. **Resolves:** whether the seven standards proposed in an
external review of the attestation brief should be adopted, and on what evidence.
**Does not touch:** `EV-NONAUTHOR-EXPOSURE-01`, which remains the blocking row.

---

## Context

An external reviewer read the attestation brief and proposed seven standards,
with a recommended sequencing: git notes and JSON Schema now, SARIF in parallel,
SCITT and TUF "the day a fork exists that the base cannot execute inside." The
reviewer flagged their own calibration honestly — SCITT's RFC status was checked,
everything else was asserted from knowledge.

Four bounded scouts were dispatched, one per technology cluster, restricted to
primary sources. Every load-bearing verdict below was then **re-verified directly**
rather than taken from a scout summary.

**Six of the seven claims are refuted or reframed. Nothing is adopted.**

## The findings

| Claim | Verdict | Primary evidence |
|---|---|---|
| SCITT delivers fork inheritance | **REFUTED** | `grep -ic 'federat' rfc9943.txt` → **0** |
| TUF/OCI distribute enforceable policy | **REFUTED** | both govern client-side verification |
| git notes = the cheap first move | **REFUTED** | see §The git notes trap |
| The ledger contract is unenforced prose | **REFUTED** | `tests/ledgercheck.py`, CI-gated |
| Trace Context as a weeks-later join key | **REFUTED** | `parent-id` mutates every hop |
| SPIFFE collapses the local-vs-CI ladder | **REFUTED** | relocates to node attestation |
| The fourth wall has no standard | **HOLDS** | nothing found; stays bespoke |

RFC 9943 itself is real: *An Architecture for Trustworthy and Transparent Digital
Supply Chains*, IETF **Standards Track**, published June 2026. The citation is
sound. The claim built on top of it is not.

### The structural finding — the one that reframes the design

**No standard can make a party you cannot execute inside enforce your policy.**
Two unrelated spec families reach the same wall:

- **SCITT §5.1.1.2:** *"The operator of a TS MAY update the Registration Policy or
  the trust anchors of a TS at any time."* If the fork operates the Transparency
  Service, the **fork** owns the policy. And §12 closes it explicitly: *"It is the
  role of the relying party to decide which TSs and Issuers they choose to trust
  for their scenario."* SCITT hands the **relying party** a choice, not the base an
  authority. That is the opposite of inheritance.
- **TUF/OCI:** the four properties are real (rollback §5.4.3.1/§5.5.4/§5.5.5,
  rotation §6.1, threshold signing §5.3.4) but they govern verification code the
  publisher does not run. A fork can decline the client, pin an old root forever,
  or strip the check from its own CI. Cryptography proves *what* was published,
  never *that the consumer chose to check*.

**Consequence: "fork inheritance" as framed is unachievable by any available
standard.** The achievable version is **detect divergence and withdraw trust** —
audit plus exit, not inherited policy. Design to that, or the design is chasing a
property that does not exist. This is a reframing, not a deferral: no future
standard release changes it, because the limit is the trust boundary itself.

### The one idea worth keeping — and socom already ratified it

SCITT's §5.1.1.2 second clause is the useful half:

> TSs MUST ensure that for any Signed Statement they register, enough information
> is made available to Auditors to reproduce the Registration checks that were
> defined by the Registration Policies at the time of Registration.

*You cannot compel the remote referent, so make the resolution state
reproducible.* An IETF standards-track RFC makes this **normative**.

**socom stated the same principle independently.** `canon/residuality.xml:95-99`:

> **compromise-recording** — When you cannot prevent, record; a detectable breach
> beats a silent one. SOCOM: the breach ledger (`socom breach`), amber gates that
> warn-and-log and feed trust scoring. **Fail it when a fail-open path leaves no
> trace.**

Convergence with an IETF RFC is **corroboration of the principle**. It is not
evidence about the tool, and it must not be cited as such.

## What socom already has — verified, not assumed

The necessary check before claiming any of this is new work:

| Property | State | Evidence |
|---|---|---|
| The principle | **RATIFIED** | `canon/residuality.xml:95-99` |
| The recording mechanism | **BUILT** | `cmd_breach` `gate.py:23`; `log_breach` `core.py:94` |
| Write-time schema enforcement | **BUILT + CI-GATED** | `tests/ledgercheck.py` parses the field contract *out of* `schemas/ledger.xml`; wired into medium + full + `.github/workflows/ci.yml:28` |
| A two-tier trust distinction | **BUILT** | `blackboard.py:513` — `"tier": "verified" if evidence else "asserted"` |
| Conformance to the principle | **VIOLATED on two measured paths** | `DEF-UNRESOLVABLE-GATE-LEAVES-NO-TRACE-01`, `DEF-BLACKBOARD-GRANTS-ON-UNREACHABLE-REMOTE-01` |
| Authenticity on distribution | **ABSENT** | `bin/socom` is served by raw `curl`; no signing anywhere in `src/socom/*.py` |
| Runner-identity tiering | **ABSENT** | the verified/asserted tier keys on *presence of evidence*, not on *where it ran* |

**The finding therefore cuts against socom's current implementation, not for it.**
socom ratified compromise-recording and then shipped two fail-open paths that
leave no trace. RFC 9943 is not a validation; it is an outside party making
normative the exact clause socom is currently failing.

### What socom already has does not reach across the boundary

The obvious hope from the table above is that having the principle **and** the
mechanism makes conformance cheap. It is cheaper than a from-scratch build, but
it does not collapse to wiring up `log_breach`, and the reason is the same wall
this document is about.

**The write site already detects the failure and already reports it**
(`blackboard.py:488-494`):

```python
bb_append(root, BB_LEASES, rec)
ok, ref, detail = bb_push(root, conf)
result["published"] = bool(ok)
if not ok:
    result["publish_error"] = detail
```

socom is **not blind**. The gap is **durability, not detection** — `published`
lives in the in-memory result, while the record appended to the shard is
byte-identical either way. That is a materially smaller problem than
`DEF-BLACKBOARD-GRANTS-ON-UNREACHABLE-REMOTE-01` reads as.

**But the mechanism socom has is on the wrong side of the boundary.**
`log_breach` (`core.py:94`) appends to `.socom/gates/breaches.log` — a **local
file**, described in its own docstring as telemetry. The consumer of a lease is a
different session on a different machine, and it never sees that log. Recording
locally that a push failed changes nothing for the party the record exists to
inform.

That is this document's structural finding appearing *inside* socom: **the
information has to reach a party you do not execute inside, and a local log never
travels.**

The read side carries its own half. `bb_fetch` fails **OPEN** — any error returns
empty shards — so a reader with an unreachable remote sees "no leases held" and
cannot distinguish that from "I could not fetch." No local breach record reaches
them either.

| Half | Gap | Shape of the fix |
|---|---|---|
| **Writer** | the durable record omits publication state | small, but the shard is append-only — no retro-stamp. Either push-before-append, or a provisional record plus a confirm record the reader joins |
| **Reader** | `bb_fetch` fails open with no trace | the compromise-recording violation proper; the half a local log cannot serve |

**Consequence for `decisions/0002`, which stays HELD.** The ruling is unchanged —
the fix mechanism is D0 against a D1 cap, first step a one-hour spike of U1 alone
— but the spike now has a sharper question to answer: **can the writer half ship
alone, or does a durable `published` flag force the reader-side join
immediately?** Answering that is what the spike is for; assuming either way is
what the cap exists to prevent.

### This proves nothing about whether socom is necessary

Stated plainly because the opposite inference is available and wrong:

- The standards solve **adjacent** problems (supply-chain artifact transparency,
  update distribution, workload identity). Their unsuitability for socom's problem
  says the problem is **unserved**. It does not say socom serves it.
- socom has the **same** limit it just found in SCITT and TUF. It cannot enforce
  inside a fork either. It is on the same side of the wall.
- Necessity is an adoption question, at proof tier **D0**, and no amount of
  standards research can move it. Only `EV-NONAUTHOR-EXPOSURE-01` can.

## The git notes trap — recorded so it is not re-proposed

git notes looks like the cheap first move and is not. Three independent failures:

1. **It does not propagate.** `git-push(1)` and `git-fetch(1)` contain **zero**
   references to notes. Every clone and CI runner needs an explicit
   `remote.<n>.fetch += refs/notes/*:refs/notes/*`, and publishing needs an
   explicit `git push origin refs/notes/*` — the identical wrapper socom already
   wrote for `BB_REF`.
2. **It dies at squash-merge.** Notes key on object SHA. `notes.rewriteRef` has no
   default, and `notes.rewrite.<command>` covers *"currently amend or rebase"* —
   cherry-pick and squash-merge are not in the list at all. A squash mints a new
   SHA, so a note bound at claim-time never reaches `main`. socom's governed repos
   squash-merge. Claim → work → merge is socom's arc; notes do not cross it.
3. **It is `DEF-BLACKBOARD-GRANTS-ON-UNREACHABLE-REMOTE-01` in a new ref name.**
   `git notes add` is a purely local object write; publication is always a
   separate, independently-failable push. That is exactly `blackboard.py:488-489`
   — `bb_append(...)` then `bb_push(...)`. Git offers no atomic add-and-publish,
   so there is no structural protection.

**The write-ordering redesign — provisional-until-published, or inverted ordering
— is required regardless of which ref layer sits underneath.** That is the real
work, it is already filed, and no ref mechanism reduces it.

## SPIFFE: the existing ladder was right

The brief assumed locally-signed claims rank below CI-signed ones. The reviewer
called that dissolvable. It is not: SPIFFE relocates the question to node
attestation, and on a laptop with no TPM the only general attestor is
`join_token`, a pre-shared secret an operator types in — trust-the-laptop-holder
wearing a different hat. Meanwhile **Sigstore Fulcio + CI OIDC is the mechanism
that justifies the original assumption**: a CI provider's OIDC issuer is a real
trust root and a laptop has no equivalent without hardware.

Keep the ladder. If local signing ever needs strengthening, TPM 2.0 / Secure
Enclave gets nearly the whole uplift with no server, no agent daemon, no
registration entries.

## Decision

1. **Adopt none of the seven.** No SCITT, no TUF, no OCI/ORAS, no SPIFFE, no git
   notes, no Trace Context. No JSON Schema — that gate exists.
2. **Reframe fork inheritance to detect-and-withdraw.** The base gets audit and
   the right to refuse. It never gets authority inside a fork.
3. **Treat compromise-recording as the load-bearing principle**, now corroborated
   by RFC 9943 §5.1.1.2 — and treat the two open defects as violations of it.
4. **Do not cite this research as evidence for socom.** It bounds the alternatives.
   It says nothing about adoption.
5. **Named-if-ever-needed, not filed as rows:** `tuf-on-ci` for policy distribution
   at fork > 0 (git-native signing via PRs, no standing signing server);
   TPM/Secure Enclave for local signing. Neither is actionable at fork = 0.

## Trigger that reopens this

**A fork exists that the base cannot execute inside** — `socom-de` inside G1, or a
first external adopter. Until then every item above is unactionable by
construction. Reopening also requires the governance-topology question SCITT does
not answer for us: one shared Transparency Service, or one per fork.

## Sources

- [RFC 9943](https://www.rfc-editor.org/rfc/rfc9943.txt) — §5.1.1 registration
  flow, §5.1.1.2 policy ownership + auditability, §12 relying-party trust choice
- [TUF specification](https://theupdateframework.github.io/specification/latest/)
  — §5.3.4, §5.4.3.1, §5.5.4, §5.5.5, §6.1
- [git-notes(1)](https://git-scm.com/docs/git-notes) ·
  [git-config(1)](https://git-scm.com/docs/git-config) — `notes.rewrite.<command>`,
  `notes.rewriteRef`
- [W3C Trace Context](https://www.w3.org/TR/trace-context/) — per-hop `parent-id`
  mutation
- [SPIRE agent config](https://github.com/spiffe/spire/blob/main/doc/spire_agent.md)
  · [OIDC in Fulcio](https://docs.sigstore.dev/certificate_authority/oidc-in-fulcio/)
- Local: `canon/residuality.xml:95-99`, `src/socom/blackboard.py:488-489,513`,
  `src/socom/gate.py:23`, `src/socom/core.py:94`, `tests/ledgercheck.py`,
  `buckets/defects.md`
