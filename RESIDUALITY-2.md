# SOCOM Residuality Analysis — Pass 2 (as-built v0.1 + human behaviour)

Pass 1 (`RESIDUALITY.md`) stressed the *naive design*. This pass stresses the
**implemented architecture** (`bin/socom` e15816c, canon/, compiled adapters,
git hooks) and adds **human-behaviour stressors** — because governance tooling
rarely dies of technical failure; it dies of normalization of deviance,
resentment, ritual compliance, and sponsor dependency.

## Production-grade verdict (honest, up front)

**v0.1 is a verified prototype, not production grade.** Evidence-based gaps
found by auditing the build against its own spec:

| Gap | Severity |
|---|---|
| G1. Generated hooks embed the builder's absolute path — any other machine gets failing hooks on first clone | critical |
| G2. `compile` overwrites CLAUDE.md/AGENTS.md unconditionally — clobbers hand-written files in adopting repos | critical (destructive) |
| G3. The CLI has zero tests — the verification tool is itself unverified | critical (credibility) |
| G4. Redaction gate (R8) spec'd, not implemented — verbatims/memories index and hydrate unscanned | high |
| G5. Orphan reaper (R12) prints worktrees, reaps nothing | medium |
| G6. Trust scoring (R11), append-only registry (R16), claims, prompt generation + claim-verify: unimplemented | medium (roadmap) |
| G7. No distribution story (PATH, install, versioning across repos) | high |
| G8. `breaches.log` is write-only — nothing ever reads it back | high (amber dies) |

## Human-behaviour stressors

| H | Stressor | Attractor it feeds |
|---|---|---|
| H1 | Deadline panic: `--no-verify` becomes habit; amber breaches accumulate unread | **Normalization of deviance** — each bypass makes the next cheaper until red bands are folklore |
| H2 | The teenager problem: rules whose *why* isn't felt breed resentment and shadow workflows | Ritual compliance / quiet uninstall |
| H3 | The single champion leaves; nobody else believes yet | Sponsor-dependency death — substrate rots in place |
| H4 | Prompt blindness: 11 principles read once, skimmed forever; compiled view too long to load attentively | Theater — the text exists, behavior doesn't change |
| H5 | First false-positive red on a deadline day → "socom is broken" → team disables hooks globally | One bad day kills adoption |
| H6 | Gaming the letter: `[test] ran it, works` satisfies the regex, not the contract | Evidence theater |
| H7 | Social memory poisoning: a confident senior writes a wrong rule; juniors and agents obey it; the falsifier field is filled in but never checked | Stale-substrate attractor with social armor |
| H8 | Breach log read as surveillance: developers feel watched, not helped; trust scores become a leaderboard | Resentment → sabotage, sandbagging, blame culture |
| H9 | Onboarding cliff: new dev clones, hooks fail (G1), first contact with socom is a broken commit | "Disable that thing" is the onboarding ritual |
| H10 | Verbatim embarrassment: preserved typos feel disrespectful when surfaced; people sanitize → signal loss; or secrets ride in verbatims (G4) | Protocol quietly edited away |
| H11 | Review theater: reviewer seat rubber-stamps under throughput pressure; "different model family" ignored for convenience | Assessment becomes a checkbox |
| H12 | Fork drift: a team copies `.socom/`, edits canon locally, never upstreams | Fleet-drift attractor, human cause |
| H13 | Maintainer burnout: untested single-file CLI grows until everyone fears touching it | Frozen substrate |

## Residues — Pass 2

**HR1 — Hooks degrade gracefully and resolve the tool, never a path.**
Hook scripts resolve socom via `command -v socom` → `$SOCOM_HOME` → repo-local
fallback; if absent they WARN and exit 0 — the substrate must never be the
reason a new developer can't commit on day one. CI remains the red floor
(R1), so graceful local absence loses nothing. Survives H5, H9, G1.
*Criticality:* also the distribution story's escape hatch (G7).

**HR2 — Compile never clobbers what it didn't generate.**
`compile` refuses to overwrite any target lacking a `socom:generated` header
(`--force` to adopt deliberately). Survives G2, H5 (a destroyed CLAUDE.md on
adoption day is an instant uninstall), H12 (local hand-edits surface as
refusals, not silent overwrites).

**HR3 — Amber must close a loop or it is noise.**
`session-start` reads `breaches.log` back: unresolved count, age, oldest
deadline — every session opens by *seeing* its debt. Breach entries record
gate + detail, **never author identity** by default: telemetry about the
*system*, not surveillance of people. Survives H1, H8, G8.

**HR4 — Substance heuristics on evidence blocks.**
`[test]` must contain something command- or output-shaped (heuristic, amber
when suspicious). Cannot fully stop H6 — but moves gaming from free to
effortful, and CI replay (R7) is the real counter. Survives H6 partially;
honest about its limits.

**HR5 — The tool tests itself, in its own gates.**
A smoke-test suite exercises every command including negative paths; it IS
`checks.fast` for this repo. A verification tool that is itself unverified
has no moral authority (H2's *why* must be felt here first). Survives G3,
H13.

**HR6 — Redaction at the substrate boundary.**
`index` and `hydrate` scan for secret-shaped strings (keys, tokens, PEM,
connection strings) and refuse to emit matching chunks. Survives G4, H10's
secrets half. (Full PII taxonomy: roadmap, with the platform classification
work.)

**HR7 — The why travels with the rule.**
Every compiled principle already carries its rationale in-line (canon text);
keep compiled views short enough to actually read — constitution first,
everything else tables and pointers. Counter to H2, H4. *Limit:* text alone
never cures H4; gates exist precisely because reading is unreliable.

**HR8 — Adoption is reversible and explicit.**
`socom init` is additive-only; nothing existing is modified without `--force`
(HR2); removing the substrate = delete `.socom/`, `socom.yaml`, generated
files. An exit that's cheap makes adoption psychologically safe. Counter to
H5, H2.

**HR9 — Upstreaming path for canon edits.**
Repo-local canon is expected to diverge (that's binding, not drift) — but
`doctor` reports the delta vs the tool's canon version so divergence is
*visible and chosen*, not accidental. Counter to H12. (Implementation:
roadmap; verdict surface exists in doctor.)

**HR10 — Falsifiers get exercised, not just written.**
Memory format requires a falsifier (R5); the closeout checklist asks "did any
memory's falsifier fire this session?" — retiring a wrong rule is a *kept*
promise, celebrated in the handoff, not an admission of failure. Counter to
H7. (Cultural residue: encoded in session.xml closeout text.)

**HR11 — No leaderboards.**
Trust (R11, when built) modulates *autonomy bands per seat*, is never
rendered as a ranking of people, and amber history expires. Counter to H8.
Design constraint recorded now, before the feature exists — one-way doors are
cheapest to avoid before they're built.

## What this pass changes immediately

Implemented in this commit: HR1 (graceful, path-independent hooks),
HR2 (no-clobber compile), HR3 (breach read-back at session-start, no authors),
HR5 (smoke tests bound as this repo's fast check), HR6 (redaction scan in
index/hydrate), HR4 (evidence-substance heuristic).

Explicitly deferred (tracked, not hidden): claims, trust scoring (with HR11
as a standing constraint), orphan reaper beyond listing, prompt generation +
claim-verification, canon-delta reporting (HR9), packaging/distribution (G7
— interim: clone + PATH, hooks survive absence via HR1).

**Re-verdict after fixes: suitable for a supervised pilot on one repo.
"Production grade" is earned at the end of the pilot, when the human residues
have been stressed by real humans — not declared by the tool's author.**
