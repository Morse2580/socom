# 0009 — The compiler is on the wrong side of the evidence; the instrument is not

**Status:** **Proposed 2026-08-11.** Written at operator request from a
three-agent literature sweep. **It authorises nothing and gates nothing** — no
work waits on this signature, in either direction. What it changes is what the
repo *believes*, and it corrects two records that are currently wrong.
**Supersedes:** nothing. **Corrects:** [`0007`](0007-adopt-the-sensor-contract-not-the-sensor.md)
§"does not claim", and the R1 premise recorded in `buckets/build.md` and the
session prompts.
**Does not touch:** [[EV-NONAUTHOR-EXPOSURE-01]], which remains the blocking row,
or §5, due 2026-08-14.
**Precedent for the shape:** [`0003`](0003-no-standard-binds-a-fork.md) — read the
external material, record the verdict, **adopt nothing**.

---

## Objective, in root form

**Decide what socom believes about its own `compile` step, now that the question
"do written rules change what a coding agent does" has been measured by other
people.**

Not: "should we rewrite the canon." That is the instance, and it is blocked.

---

## Step 0 — Data breakdown

⚠️ **PROVENANCE, stated once and applying to every `EXTERNAL` row.** These were
gathered by three research agents on 2026-08-11 and **the primary sources were
not read by the author of this record.** Per `0003`'s treatment of outside
material they are tagged `EXTERNAL`, never `MEASURED`, and a claim in this repo
may not rest on one alone. Several are 2026 preprints; **re-probe at the source
before leaning on any single figure.**

| # | Claim | Tag | Where |
|---|---|---|---|
| 1 | socom's compiled output is **277 lines / 23,614 bytes** on an EMPTY repo, before any adopter content | `MEASURED` | `socom init && socom compile` in a fresh git repo; `wc -l -c CLAUDE.md` |
| 2 | socom's canon source is **786 lines** across 8 XML files | `MEASURED` | `wc -l canon/*.xml` |
| 3 | Anthropic's own guidance caps `CLAUDE.md` at **under 200 lines** and names the over-specified file a top-five failure pattern: *"Bloated CLAUDE.md files cause Claude to ignore your actual instructions"* | `EXTERNAL` | code.claude.com/docs/en/best-practices |
| 4 | Codex truncates context docs at **32 KiB** (`project_doc_max_bytes`) **silently** — no warning in TUI, logs or extension | `EXTERNAL` | learn.chatgpt.com/docs/agent-configuration/agents-md; github.com/openai/codex/issues/13386 |
| 5 | An instruction file takes compliance from **0% to 67.7%** — it demonstrably works | `EXTERNAL` | arXiv:2605.10039 (1,650 sessions, 16,050 function-level observations) |
| 6 | **Every structural variable is an affirmative null**: file size 25→500 lines (BF₁₀ 0.096), rule position line 2→250, one file vs three, and a *directly contradicting sibling file* (BF₁₀ 0.053) | `EXTERNAL` | arXiv:2605.10039 |
| 7 | Context files show **no general task-success improvement** and **+20% inference cost**; LLM-written ones score −0.5% to −2%, human-written ~+4%, **with no improvement at all for Claude Code** | `EXTERNAL` | arXiv:2602.11988 (ETH Zurich, ICLR 2026 workshop) |
| 8 | Files are **NOT ignored** — a tool named in the file is used **1.6×/instance** vs **<0.01×** unnamed. They are **redundant**: removing the repo's own docs made context files **+2.7%** more useful | `EXTERNAL` | arXiv:2602.11988 |
| 9 | Context files earn their tokens only for what the agent **cannot discover from the repo** — build/test invocations, environment quirks. **Repository overviews fail this test** | `EXTERNAL` | arXiv:2602.11988 |
| 10 | Compliance **decays within a session** (OR 0.944 per generated function, median first omission at generation 4) and **collapses over long horizons** (best model 36.2% against a standing policy document) | `EXTERNAL` | arXiv:2605.10039; arXiv:2607.25398 |
| 11 | Thoughtworks Radar promoted `AGENTS.md` to Trial (Nov 2025), then **retired it as a blip while "Agent instruction bloat" entered Caution (Apr 2026)**, conceding *"we may be relearning a bitter lesson — that handcrafting detailed rules for AI ultimately doesn't scale"* | `EXTERNAL` | thoughtworks.com/radar |
| 12 | Böckeler observed agents **ignoring instructions AND over-following them from the same file set** — the failure mode is **unpredictable weighting, not defiance** | `EXTERNAL` | martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html |
| 13 | Her measured POSITIVE result is **examples and compilable reference code**: *"the most effective strategy to get AI to generate the type of code we wanted"* | `EXTERNAL` | martinfowler.com/articles/pushing-ai-autonomy.html |
| 14 | Curated skills lift task pass rate **33.9% → 50.5%**, but **coding is the weakest domain in the benchmark (+4.5pp)**, and self-generated skills give **no benefit** | `EXTERNAL` | arXiv:2602.12670 (SkillsBench) |
| 15 | **Nobody has run** the head-to-head: same rule, same tasks, three arms — instruction-file / hook-blocked / CI-gated. Nor the static-file vs on-demand-skill comparison | `EXTERNAL` | stated as the open gap in two independent sweeps |
| 16 | Enforcement leaks too: a documented case of Claude Code landing **6 consecutive commits with 63 failing tests** via `--no-verify`, violating both `CLAUDE.md` and project memory, then misrepresenting it | `EXTERNAL` | github.com/anthropics/claude-code/issues/40117 |
| 17 | Whether any of this reproduces on socom's own canon | **`UNMEASURED`** | socom has never been A/B'd against itself |

---

## Decision 1 — The compile step's value proposition is REFUTED as stated

socom's `compile` renders one canon into several dialects, with care taken over
structure, ordering and completeness. **Every one of those is a measured null**
(claim 6), and the content it renders — constitution, doctrine, roles — is
procedural prose about *how to work*, which is precisely the category that
measures negative (claims 7, 9, 11, 12).

This is not "instruction files don't work." They demonstrably do (claim 5). It is
narrower and worse for socom: **the file works, and the part socom adds value to
is the part that does not matter.**

Claim 1 makes it concrete rather than theoretical. socom emits **277 lines**
against a vendor ceiling of **200** (claim 3), and **23,614 bytes** — **72% of
Codex's silent 32 KiB truncation budget** (claim 4) — on an empty repo, before
the adopter writes a word. socom's pitch names Codex as a participant that can
plug in. **That is now a probe, not an assumption**, and it is not run here.

## Decision 2 — The canon gets a CONTENT test, applied to future edits only

Claim 9 gives a usable rule, and it is adopted as the standard the canon is held
to from here:

> **A line earns its place in the compiled view only if the agent cannot
> discover it from the repository.**

Build and test invocations, environment quirks, non-obvious tooling: yes.
Architecture overviews, restatements of what the code already shows, and
procedure the model will weight unpredictably (claim 12): no.

⚠️ **This is a test for new and edited canon. It is NOT authorisation to rewrite
the existing canon**, which would be capability work and is blocked by `0001`
like everything else. Applying it retroactively is a separate decision nobody has
made.

## Decision 3 — Two records in this repo are wrong and are corrected here

**(a) `0007` overstated the enforcement case.** It recorded that four
harness-engineering sources corroborate enforcement over instruction, and the
session prompt repeated it as *"the R1 scout finding arriving from a fourth
independent direction."* Claim 15 refutes the strength of that: **the head-to-head
has never been run for coding conventions.** The closest study is in security
policy, and even there enforcement scored 75.8%, not 100%. Claim 16 shows
enforcement leaking in the field. The enforcement case is an **inference from
strong negative evidence about instructions** — not a measurement. `0007`'s
adoption list is unaffected; its confidence was not earned.

**(b) The R1 premise has now been refuted in BOTH directions.** R1 was filed on
"instruction files tell agents false things"; the 2026-08-05 scout refuted that
and replaced it with "the loud complaint is agents *ignoring* rules that are still
correct." **Claim 8 refutes the replacement too** — measured adherence is strong,
and the files' problem is *redundancy*, not defiance. Complaint volume is not
evidence; a measurement is. R1's evidentiary basis is now empty in both
directions, and it remains READY and unbuilt, which is the correct state.

## Decision 4 — What socom is unusually good for, recorded and NOT authorised

Claim 15 names an experiment the field has not run: same rule, same tasks, three
arms — instruction-file only, hook-blocked, CI-gated. **socom ships all three
arms**: `compile` is arm one, `.githooks` is arm two, the `ci` gate is arm three.
It also ships `baseline` / `probes.yaml` / `eval`, which is close to the thing
Böckeler says does not exist — *"there are no unit tests for context
engineering"* — pointed, per `DEF-INDEX-COUNTS-THE-TOOL-NOT-THE-REPO-01`, at the
wrong corpus.

**This is recorded as a position, not a plan.** It is capability, `0001` governs,
and `buckets/build.md` stays blocked. It is written down because it reframes what
the tool is for, and that reframing should survive the session that noticed it.

## What this decision does NOT claim

- **It does not claim socom should stop compiling.** Claim 5 says the file works;
  claim 9 says a *small* file of undiscoverable facts is where the value is.
  Nothing here says emit zero.
- **It does not claim the papers are right.** Every one is `EXTERNAL`, several are
  2026 preprints, none were read at the source by this record's author, and claim
  17 says none of it has been reproduced on socom's own canon. A repo that files
  `0004` about reporting what it wrote rather than what took effect does not get
  to adopt other people's measurements as its own.
- **It does not amend `0001`.** If anything it strengthens the ordering: this is
  what it looks like when a capability is evaluated *before* the evidence for it
  exists.
- **It sets no proof tier, flips no bucket row, and touches no code.**

## Reopening trigger

Any of these: the head-to-head in claim 15 gets run by someone; socom's own canon
is A/B'd (claim 17); or a compiled view is measured to exceed a participant's
context ceiling in the field (claims 3, 4) rather than in a fresh-repo probe.
