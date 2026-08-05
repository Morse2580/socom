# Defect bucket

Work whose deliverable is **behaviour the tool already ships and already claims,
made true**. Not a capability, not a fact about the world.

Governed by [`../decisions/0001-exposure-before-capability.md`](../decisions/0001-exposure-before-capability.md)
§Amendment 1, which bounds this lane so it cannot become a build lane under
another name:

1. A row here repairs what socom **already ships and already claims**. Anything
   that adds a surface, knob, mechanism, or authorization absent from `bin/socom`
   today is a capability → `build.md`, `BLOCKED`. **When in doubt it is a capability.**
2. **`P0` is only for defects that fire before a non-author's stall point** — the
   ones that would corrupt [[EV-NONAUTHOR-EXPOSURE-01]] by burning a scarce
   participant on something already recorded here. That is the whole
   pre-exposure budget. Everything else is `P1` and waits.
3. A defect the exposure measurement is **supposed to discover** is not repaired
   first — repairing it deletes the finding. Recorded `P1` with the reason stated.

**Provenance.** Every row below was found on 2026-08-03 by five independent
cold-run agents (Go/K8s, TypeScript, Python, Rust, staff-polyglot) each given
only the public GitHub link, on `kubernetes-sigs/descheduler`, `pmndrs/zustand`,
`petl-developers/petl`, `tokio-rs/axum`, `psf/requests` — then adversarially
re-verified against source and re-run from primary artifacts. Claims marked
**VERIFIED** were reproduced by hand.

---

## Done — the pre-exposure P0 budget (all four, 2026-08-03/04)

> ⚠️ **These four were marked DONE once prematurely, and adversarial
> verification reopened one of them.** `DEF-HOOKS-HIJACK-NO-UNADOPT-01` was
> closed against the sub-case it was written from (`core.hooksPath` already SET)
> while **the same defect was still fully live for a repo whose hooks are in the
> default `.git/hooks/`** — which is where lefthook installs. `PILOT.md` shipped
> a safety claim naming lefthook that was false at the time it was written.
> Three further defects (an adopt crash, silent deletion of a user's
> `.gitignore` rule, and `unadopt` performing the very clobber it exists to
> undo) were introduced by the repairs themselves. All are now fixed and
> regression-tested; the audit trail is in each row.
> **The lesson is in the ordering:** every one of these survived `gate full`,
> `build.py --check`, and a 323-test suite. Green gates measured the half of the
> change that had tests. The half that touched the adopter's repo had none.

Repaired and verified in one session. Each row keeps its original text; the
**VERIFIED-FIXED** line at the end of each is the evidence against its own
falsifiable acceptance, re-run on the shipped binary after the last edit.

The lane is now empty of P0s, which is the only state in which
[[EV-NONAUTHOR-EXPOSURE-01]] can spend a participant on something *not* already
written down here. **That row is still unrun, and it is still the work.**

- `DEF-HOOKS-HIJACK-NO-UNADOPT-01` **DONE P0** — **`adopt` silently overwrites
  the adopting repo's `core.hooksPath`, disabling every hook it already had, and
  there is no way back.** VERIFIED at `src/socom/lifecycle.py:380` `_wire_hooks`:
  it reads the current value and, if it is anything other than `.githooks`,
  runs `git config core.hooksPath .githooks` **unconditionally** — no check for a
  pre-existing value, no warning, no record of what it replaced. A repo on husky
  (`core.hooksPath=.husky`), lefthook, or its own convention has its lint-staged,
  its commit-msg validator and its secret scanner stop running at
  `socom quickstart`. There is **no repo-level exit**: `cmd_uninstall`
  (`install.py:83`) removes the `~/.local/bin/socom` symlink and nothing else,
  there is no `unadopt` in the dispatch table, and since the prior value was
  never recorded socom **cannot restore it even in principle**.
  ⚠️ **This falsifies `PILOT.md`'s bolded safety claim**, stated under "Is it
  safe? (read this first)": *"SOCOM is **additive and non-destructive**: it
  plants files (never clobbers your edits), wires git hooks that run *your own*
  commands."* It clobbers a git config, and for a repo that already had hooks,
  "runs your own commands" is false — they stop running.
  **Why P0 and why above every other row:** [[DEF-ADOPTION-REDDENS-HOST-GATE-01]]
  makes a repo's gates loudly **red** — visible, annoying, fixable. This makes
  the adopter's existing gates silently **pass**. The discovery mode is "a secret
  got committed and we found out why later," and a stranger who learns socom
  disabled their safety net does not run it a second time, and tells their team.
  ⚠️ **All five cold runs missed this**, for one shared reason: they snapshotted
  the *filesystem* (which is how the other three P0 rows were found) and none
  snapshotted `git config`. A common blind spot, not five independent misses —
  and the reason a defect this severe survived a five-agent sweep.
  **Falsifiable acceptance:** adopting into a repo with `core.hooksPath` already
  set to something else does not silently change it — socom records the prior
  value and either refuses or warns; and there is a path that restores the repo
  to its pre-adopt hook state. **Files:** `src/socom/lifecycle.py`,
  `src/socom/install.py`, `src/socom/cli.py`, `PILOT.md`.
  **VERIFIED-FIXED.** `_wire_hooks` now returns `wired|foreign|nogit` instead of
  a bool — the three cases were never interchangeable, and collapsing them is
  what hid the destructive one. Verified against a **real `husky@9.1.7`
  install** (`npm i -D husky && npx husky init`), not a hand-written stand-in:
  | binary | `core.hooksPath` after `adopt` | husky's hook on next commit |
  |---|---|---|
  | PRE-FIX | `.husky/_` → **`.githooks`** | **silent — never ran** |
  | SHIPPED | `.husky/_` (unchanged) | ran |
  `socom.priorhookspath` records `.husky/_`.
  ⚠️ **Why the real install mattered.** The first pass used a fixture written by
  hand that set `core.hooksPath=.husky`. Real husky v9 sets **`.husky/_`** — the
  fixture had guessed the value wrong. The repair keys on "non-empty and not
  ours" so its behaviour was identical either way, but the fixture could not have
  shown that, and a fixture the author wrote is not evidence about a tool the
  author did not write.

  ⚠️⚠️ **REOPENED 2026-08-04 by adversarial verification, then closed properly.**
  Everything above was true and the row was still **not fixed**, because the
  guard keyed on `core.hooksPath` being non-empty — i.e. it treated *unset* as
  "this repo has no hooks". Unset means **"use the default `.git/hooks/`"**, and
  that is where **lefthook installs** and where a hand-written hook lives.
  REPRODUCED on the shipped binary: a `.git/hooks/pre-commit` that blocked a
  commit before adopt stopped running after it, adopt printed
  `✓ git hooks wired — local gates live`, and the commit landed. Confirmed
  again against a real `lefthook@2.1.10` install. The row's own problem
  statement names lefthook, and `PILOT.md` asserted socom "refuses and changes
  nothing" for it — **false as shipped.**
  **Fix:** `_default_hooks_present` — executable non-`.sample` files under
  `git rev-parse --git-path hooks`. Unset + real hooks present is now `foreign`,
  with its own message. Verified: `.git/hooks` repo → refused, host hook still
  fires; real lefthook → refused, lefthook blocks the commit (rc=1, no commit
  object); ordinary repo with no hooks → still wires normally (non-vacuity).
  **Two more defects the repairs themselves introduced, both found by
  verification and both fixed:**
  · **`unadopt` performed the exact clobber it exists to undo.** It restored
    from `socom.priorhookspath` without checking the current value was still
    socom's, and the record is written once and never invalidated. REPRODUCED:
    adopt, then `git config core.hooksPath .husky`, then `unadopt` — husky
    silently disabled, while printing *"it was unset before adopt"* as if it
    described the present. Now refuses unless `core.hooksPath == .githooks` and
    prints the recorded value plus the exact command to apply it by hand.
  · **Scope infidelity.** `_git_hooks_path` reads the EFFECTIVE value across
    global/system, but the record and restore write LOCAL — so a repo inheriting
    a global hooks path got that value pinned into its local config by
    `unadopt`, silently detaching it from the org setting it should keep
    following. Now records `--local` only.
  adopt reports the refusal on stderr with both ways forward. New `socom
  unadopt`: restored `.husky` after a deliberate switch (host hook ran again),
  and on a plain repo returned `core.hooksPath` to **unset** with 0 residual
  `socom.*` keys. The prior value is recorded once, so a second `adopt` cannot
  overwrite the record with socom's own value. `PILOT.md`'s safety section now
  enumerates every write socom makes to something already yours, and names the
  way back — the claim is checkable instead of trusted.

- `DEF-COMMIT-GATE-REJECTS-HOST-CONVENTION-01` **DONE P0** — **The commit gate
  rejects the majority of the adopting repo's real commits, using a rule it never
  prints, with an error that misnames itself.** VERIFIED at `src/socom/gate.py:62`:
  `COMMIT_RX = ^(feat|fix|chore|refactor|test|docs)\([a-z0-9._-]+\): .+` — a
  hardcoded module constant with a **mandatory** scope and no `perf|ci|wip|revert|style|build`.
  Recomputed against zustand's real history (after `--unshallow`; the artifact
  shipped as a 2-commit shallow clone): **40 pass / 60 REJECTED of the last 100
  upstream subjects.** Rejected include zustand's upstream HEAD at clone time
  (`fix: update broken README links…`, no scope), release commits (`5.0.14`), and
  `test(middleware/immer): add runtime tests` — fully conventional, rejected
  because `/` is outside the scope charset. Akili's own `CLAUDE.md:802` mandates
  `perf ci wip`; all three are rejected. The error (`bin/socom:2678`) says *"first
  line must be 'type(scope): description'"* and then echoes back a subject that
  **is** exactly that, never printing the allowed set — 3/5 agents had to grep the
  binary to learn the real rule.
  **Why P0:** it blocks the single most frequent action a developer takes, on run
  #1, with a rule that is not the adopting repo's. `PILOT.md`'s report list opens
  with *"Did you reach for `git commit --no-verify`?"* — this row is that moment,
  and p3 named it verbatim: *"the moment I would have typed `--no-verify` on a
  normal workday."*
  ⚠️ **Repair only.** Widen `COMMIT_RX` to the conventional-commit type set with
  an optional scope, and print the rule that fired on rejection. Making the set
  **configurable** is a new knob → [[SUBSTRATE-COMMIT-TYPES-CONFIGURABLE-01]], BLOCKED.
  **Falsifiable acceptance:** a rejection prints the rule and the allowed set;
  and ≥90% of the adopting repo's last 100 subjects pass on a repo that follows
  conventional commits. **Files:** `src/socom/gate.py`.
  **VERIFIED-FIXED.** `COMMIT_RX` is now close to the Conventional Commits
  v1.0.0 shape — optional scope, `[^()]+` scope charset, optional `!`, the
  spec's type set plus `revert`/`wip`, and a description that must contain a
  non-space character. The RED message prints the rule, the full type list, and
  two examples.

  **Acceptance, measured honestly.** Merge commits are identified by **parent
  count** — what git itself uses — and excluded, because at commit time they are
  skipped via `MERGE_HEAD`, not via anything about their text. Percentages are
  over ORDINARY (single-parent) commits in each repo's last 100:

  | repo | commits | merges | ordinary | pass |
  |---|---|---|---|---|
  | electron/electron | 100 | 0 | 100 | **100%** |
  | socom (self) | 100 | 21 | 79 | **100%** |
  | nestjs/nest | 100 | 50 | 50 | **98%** |
  | angular/angular | 100 | 0 | 100 | **96%** |
  | angular/components | 100 | 0 | 100 | **95%** |
  | vuejs/core | 100 | 0 | 100 | **92%** |
  | ionic-team/ionic-framework | 100 | 12 | 88 | **73%** ← counterexample |
  | pmndrs/zustand | 100 | 0 | 100 | 66% |

  ⚠️ **An earlier draft of this row reported the rate over all 100 subjects with
  merges waved through by a SUBJECT-TEXT exemption.** That was contaminated —
  a text exemption is spoofable, so on a merge-heavy repo the number could not
  fail, and socom's own headline "75%→100%" was partly measuring the exemption
  rather than the fix. The exemption is now state-based (see the ⚠️⚠️ note
  below), and the table above re-derives every figure by parent count. The fix
  is independently real: on the zero-merge repos, where no exemption of any kind
  applies, angular went 48→96% and electron 1→100%.

  ⚠️ **The acceptance criterion as written is falsified, and this is the honest
  statement of it.** `ionic-team/ionic-framework` **does** follow the convention
  — `docs/CONTRIBUTING.md`: *"We follow the [Conventional Commits
  specification]"*, CI-enforced — and scores **73%**, not ≥90%. Its 23 rejects
  are exactly two shapes: **12 × `chore():`** (an EMPTY scope) and **11 ×
  `v8.8.16`** (a bare version subject). Neither is sanctioned by the spec, and
  admitting them is the BLOCKED knob
  [[SUBSTRATE-COMMIT-TYPES-CONFIGURABLE-01]] — so the *repair* is not at fault,
  but "≥90% on a repo that follows conventional commits" is too strong as a
  criterion. It holds only for repos whose subjects are themselves conventional.
  A repo can follow the convention *as policy* and still emit release and
  lockfile commits that are not.

  ⚠️ **Known divergence from the spec, stated rather than papered over.** The
  spec says the units of information *"MUST NOT be treated as case-sensitive"*,
  so `Fix: correct a typo` is spec-valid and socom RED-blocks it. socom matches
  commitlint's `config-conventional` here (`type-case: lower-case`) rather than
  the spec text, which is defensible tooling behaviour — but it means "implements
  Conventional Commits v1.0.0" is an overstatement on that clause.

  The cohort repos stay below 90% (zustand 66, axum, petl, descheduler,
  requests) because they genuinely do not follow the convention.
  ⚠️ **Scope call made during the repair, flagged rather than assumed.** The
  hook fires on `git merge` too, so the gate RED-blocked merge commits on a
  subject git writes itself — reproduced: `git merge --no-ff side` aborted with
  *"Not committing merge"*. socom's own last 100 subjects contain **21** of
  them. Judged repair, not capability: same single gate, nothing configurable,
  no new surface — but it is a widening the row did not name, so it is recorded
  here rather than buried.
  ⚠️⚠️ **The first cut of that widening was itself a defect, and a worse one
  than the row it served.** It matched a leading `Merge `/`Revert "`/`fixup!`
  on the SUBJECT (commitlint's default posture), which means the gate could be
  defeated by *typing* it. VERIFIED on a scratch repo with socom's hooks wired:
  the subject `Merge in my sloppy change with no blocks at all` **committed
  cleanly** — no type, no `[what]`, no `[test]`, not even an amber. Anyone who
  found it once had a permanent one-word bypass of the entire commit gate.
  **Root fix: discriminate on repo STATE, not on text.**
  `_git_authored_commit` checks `MERGE_HEAD` / `REVERT_HEAD` /
  `CHERRY_PICK_HEAD` under `git rev-parse --git-dir` — verified present during
  a real merge and absent during an ordinary commit. The message is what the
  author controls; `MERGE_HEAD` is what git controls, and only the latter can
  discriminate here. Autosquash has no state file, so `AUTOSQUASH_RX` strips
  `fixup!`/`squash!`/`amend!` and validates **what the autosquash targets** —
  so the strip cannot launder a bad subject.
  Verified end-to-end with real commits, five cases: real `git merge --no-ff` →
  passes (*"skipped — git authored this message (merge in progress)"*); real
  `git revert` → passes; the bypass subject → **RED, no commit object created**;
  `fixup!` of a conventional subject → passes; `fixup! sloppy change` → RED.
  Known edge, accepted rather than patched: `git commit --fixup=HEAD` where HEAD
  is itself a merge/revert commit is rejected, because the target subject is not
  conventional. Narrow — and adding one more special case is exactly how the
  bypass got in.
  Non-vacuity control: `'updated some stuff'` still RED-blocks, a conventional
  subject still commits.

- `DEF-ADOPTION-REDDENS-HOST-GATE-01` **DONE P0** — **quickstart binds the gates
  to the repo's test command, and its own generated files then fail that command.**
  VERIFIED by controlled 4-cell experiment on zustand: pristine `src/vanilla.ts`
  with socom's files stashed → `npm test` **RC=0, 214 passed, prettier lists zero
  files**. Same pristine source with socom's files restored → `npm test` **RC=1**,
  `prettier . --list-different` lists **exactly 16 files, all 16 written by socom**
  (7 × `.claude/agents/*.md`, `CLAUDE.md`, `AGENTS.md`, `socom.yaml`,
  `.gitlab-ci.yml`, `.github/workflows/socom-gates.yml`,
  `.socom/ci/azure-socom-gates.yml`, `.socom/index/probes.yaml`,
  `.socom/index/vectors.json`, `.socom/lessons/index.md`). Spec suite untouched in
  both cells. socom.yaml binds `checks.{fast,medium,full}: "npm test"`, and
  `npm test` includes `test:format`.
  p2: *"every gate in the repo is now permanently red for reasons unrelated to my
  code, which is precisely how teams learn to ignore gates."*
  **Falsifiable acceptance:** adopt on a repo whose format check is green; it is
  still green immediately after `quickstart`, with no hand edits.
  **Files:** `src/socom/lifecycle.py`, `src/socom/install.py`, `templates/`.
  **VERIFIED-FIXED.** Re-ran the experiment on a fresh `pmndrs/zustand` clone
  (upstream HEAD `beca84e`) with the dependencies really installed
  (`pnpm install --frozen-lockfile`), driving the repo's **own `npm test`** —
  not just the `test:format` sub-check:
  | cell | `npm test` |
  |---|---|
  | pristine | **RC=0** — 13 files, 214 tests passed; spec/types/format/lint all Done |
  | adopted, PRE-FIX binary | **RC=1** — `test:format: Failed`, listing socom's own files |
  | adopted, SHIPPED binary | **RC=0** — 214 tests passed, all four sub-checks Done |
  The middle cell is the discriminating control: same command, same clone, only
  the binary differs, so the green is attributable to the repair and not to a
  quirk of the checkout.
  ⚠️ **An earlier draft of this line said "re-ran the 4-cell experiment" while
  having actually run only `prettier . --list-different`** — the exact body of
  the `test:format` script, but one of four cells. The claim was ahead of the
  evidence; the table above is the real thing. Recorded rather than quietly
  overwritten, because this bucket's rows are the substrate's own audit trail. `adopt` now writes a marked block into
  `.prettierignore` naming the 14 socom-generated paths it found. Root fix, not
  a formatting patch: socom emits files into someone else's repo and had never
  told that repo's tools which files are socom's — so the same mechanism serves
  `DEF-RUNTIME-STATE-UNIGNORED-01`, and emitting prettier-shaped YAML would have
  fixed neither. Membership is PROVED by the `socom:generated` header, never
  assumed from the path, so a repo that owns its own `.gitlab-ci.yml` does not
  find it silently excluded from its own formatter. `.prettierignore` is written
  only when the repo actually runs prettier (config file or package.json dep) —
  prettier is the only common formatter that claims md/yaml/json, which is the
  whole of socom's emitted surface.

- `DEF-RUNTIME-STATE-UNIGNORED-01` **DONE P0** — **socom plants machine-local
  runtime state and writes no `.gitignore` entry for it, so a routine `git add -A`
  commits it.** VERIFIED 5/5: no `.gitignore` entry in any of the five repos, and
  `grep -rn gitignore src/socom/ templates/` → **zero hits**; socom never touches
  `.gitignore` on any path. Addable state confirmed in zustand: per-PID lease
  shards (`.socom/blackboard/leases/*.jsonl`), the per-machine breach log, and
  `.socom/index/{vectors,chunks}.jsonl` — `git check-ignore -v` rc=1 on all.
  On a team these conflict on every branch. p3 hit the sharper version: `git add -A`
  swept the substrate into a code commit, and `git revert` on that commit then
  **deleted socom from the worktree**.
  Supporting evidence: **Akili's own `.gitignore` carries `.socom/` at lines
  424–430 with a hand-written rationale** ("per-clone working cache, never
  source"). A human had to write that. socom never emits it.
  **Falsifiable acceptance:** after `quickstart`, `git status --porcelain -uall`
  shows no machine-local runtime state as untracked-and-addable.
  **Files:** `src/socom/lifecycle.py`.
  **VERIFIED-FIXED.** `adopt` writes a marked block into `.gitignore` (6
  patterns) via the same mechanism as the prettier block. On the zustand clone,
  after `quickstart` **plus** a real `socom claim` that materialised a per-PID
  lease shard, `git add -A` staged **0** runtime-state files (32 staged, all
  substrate source). `git check-ignore`: `breaches.log`, `vectors.json`,
  `chunks.jsonl`, the lease shard → IGNORED.
  ⚠️⚠️ **Two defects the repair itself introduced, found by verification,
  both fixed and regression-tested.** `_ensure_ignore_block` checked only that
  both markers were PRESENT, then split on the first of each:
  · **adopt CRASHED** (`ValueError: not enough values to unpack`) when the
    markers were out of order — which a plain `sort` on `.gitignore` produces,
    since `<` sorts before `>`. It died *before* hook wiring, so every retry
    failed at the same line: an adopter in that state could never wire hooks,
    with no message saying why.
  · **It SILENTLY DELETED user-authored lines.** Delete the END marker (one
    edit) and the next adopt appends a second block; the adopt after that
    rewrites everything between the first BEGIN and the first END — eating any
    rule in between. REPRODUCED: a user rule present after adopt #2 was gone
    after adopt #3, with the only output being the green *"`git add -A` is
    safe"* checkmark. The docstring claimed content outside the markers was
    left byte-for-byte; it was not.
  **Fix:** count the markers before any surgery. Exactly one of each, in order,
  or the file is `malformed` and socom **touches nothing** and says so loudly on
  stderr — an ignore file belongs to the adopter, and the only safe failure is
  to leave it alone. 13 regression tests in `tests/unit.py` cover reversed,
  duplicated, and half-deleted markers, plus the happy paths.
  ⚠️ **The `.socom/` split is the load-bearing part of this repair, and the
  reason it is not just Akili's line copied in.** Akili's hand-written
  `.gitignore` ignores **all** of `.socom/`; socom must not, because canon,
  probes, lessons and memory are the substrate's SOURCE and have to travel with
  the repo — ignoring them wholesale would silently un-share the substrate on
  the first teammate's clone, trading a visible defect for an invisible one.
  Only regenerable per-machine state is ignored. Asserted both directions:
  `canon/constitution.xml`, `index/probes.yaml`, `lessons/index.md`,
  `memory/INDEX.md` all still committable. `.socom/` as a whole IS excluded from
  the prettier block, where excluding it is right — none of it is the host's to
  format.

## Active — P1 (recorded; explicitly NOT pre-exposure)

- `DEF-CI-ADAPTER-CLAIMS-UNINVOKED-GATE-01` **READY P1** — **All three generated
  CI adapters name a socom gate and invoke no socom.** VERIFIED 5/5: every
  `.github/workflows/socom-gates.yml` has step name
  `re-assert checks.full (socom gate, R1)` and `run:` = the raw `checks.full`
  string (`./test/run-unit-tests.sh`, `npm test`, `cargo test`, …). The only
  occurrences of "socom" in the file are the generated header, `name: socom-gates`,
  and the step's display name. It `pip install pyyaml` — socom's only dependency —
  and then never calls it. The same holds for the generated `.gitlab-ci.yml` and
  `.socom/ci/azure-socom-gates.yml`. So the amber/red band semantics are **absent
  in CI**, exactly where `README` promises *"CI re-asserts them"*. Also no
  `actions/setup-go` on a Go repo. **Scope: repair only** — emit `socom gate <id>`
  so the step does what its name says. Anything wider is capability.
  **P1 not P0:** a stranger on run #1 does not push and watch CI.
  **Falsifiable acceptance:** the generated workflow invokes `socom gate`, and a
  band violation fails the job. **Files:** `src/socom/lifecycle.py`.

- `DEF-BLACKBOARD-UNDISCOVERABLE-FROM-GENERATED-DOCS-01` **READY P1** — **The
  blackboard is absent from every artifact socom generates for the runtime that
  is supposed to consume it.** VERIFIED 5/5 across the generated CLAUDE.md and
  AGENTS.md (23,745 bytes each on descheduler): `attest` = **0**, `blackboard` =
  **0**, and zero occurrences of any `socom claim` / `socom attest` invocation.
  The sweep is broader than first written: also zero across all 7
  `.claude/agents/*.md`, `.claude/settings.json`, `.cursor/rules/socom.mdc`, and
  all 20 files under `.socom/`. socom also writes **no `.mcp.json`** on adopt, so
  the blackboard is not wired into the adopting repo at all.
  ⚠️ **Two corrections to the first draft of this row, both from re-verification:**
  `claim` is **not** 0 — it appears on 11 lines of the generated CLAUDE.md as
  English ("domain-scoped **claims** with TTL auto-expiry"), so an agent learns
  claims exist but never learns the command. And *"the only documentation is the
  Python docstring"* is **false** — `socom --help` documents all five blackboard
  verbs in prose. The defensible claim is narrower: **discovery requires leaving
  the generated docs and running the bare binary, and nothing the agent reads at
  session start points there.**
  Compounding footgun, VERIFIED: `socom attest --help` is unhandled and falls
  through to an arg error — and **`socom claim --help` does not print help, it
  acquires an 8h lease on a path literally named `--help`**, under an identity
  that dies with the shell and (per [[R3-LEASE-IDENTITY-DURABLE-01]]) cannot then
  be released.
  **P1 not P0:** it costs a second use only for someone who wanted the blackboard,
  and decision 0001 demoted the blackboard to an instrument.
  **Falsifiable acceptance:** an agent given only the generated CLAUDE.md can
  attest and claim without reading socom's source; and `<verb> --help` prints help
  for every verb rather than executing. **Files:** `src/socom/lifecycle.py`,
  `src/socom/cli.py`, `templates/`.

- `DEF-LEDGER-GATE-BAND-HARDCODED-01` **READY P1** — **Every ledger row socom has
  ever written mislabels its band.** VERIFIED at `src/socom/ledger.py:153`:
  `_ledger_row` hardcodes `"gate_band": "red"`, and both writers go through it.
  `schemas/ledger.xml:30` declares the enum correctly
  (`fast|medium|full|ci|red|amber`), so the schema is right and the writer lies.
  `gate task-completion` is tier `fast` (`gate.py:211`) and still records `"red"`.
  Confirmed in real cohort data: both rows in p4's axum ledger read
  `gate_band=red`, one of them with `exit=0 verdict=kept` — a **passing** run
  stamped red band, written by `contract verify --record` rather than any red gate.
  **Why it is filed separately:** it is a **prerequisite** for any status claim
  derived from the ledger ([[SUBSTRATE-STATUS-TIER-SWEEP-01]]), not a sub-clause
  of one — the band must be true before anything can be derived from it.
  **Falsifiable acceptance:** a recorded row's `gate_band` matches the tier that
  actually ran, asserted by `tests/ledgercheck.py`. **Files:**
  `src/socom/ledger.py`, `tests/ledgercheck.py`.

- `DEF-BLACKBOARD-GRANTS-ON-UNREACHABLE-REMOTE-01` **READY P1 — highest-severity
  P1 in this bucket** — **When the remote is unreachable, `claim` grants a lease
  it would have refused, and the record it writes is byte-identical to a
  published one. Two sessions end up both holding the same path, each `--scan`
  reporting itself as the sole holder.** Same class as
  [[DEF-UNRESOLVABLE-GATE-LEAVES-NO-TRACE-01]], applied to the collision-
  prevention mechanism instead of the gates — and worse there, because a lease's
  *entire function* is to be visible to other sessions. A local-only lease is not
  a degraded lease; it is a no-op that reports success.
  **MEASURED (n=1 controlled A/B, two clones of one bare remote, 2026-08-05,
  `caa677a`).** Distinct `SOCOM_SESSION` authors, same path:
  - **Control, remote reachable:** A acquires; B is refused —
    `HELD by sessionA … not granted — yield, pick other paths, or wait for the TTL`.
  - **Variable, B's remote unreachable:** B is **granted** —
    `acquired src/other.py as sessionB [l-0ed53feab637] (LOCAL ONLY — not published: …)`,
    **exit 0**. `claim --scan` then shows A holding it in A, B holding it in B.
  - **The record on disk** (`.socom/blackboard/leases/<author>.jsonl`) carries
    `kind/author/ts/paths/intent/ttl_s` and **no published field** — `bb_do_claim`
    (`blackboard.py:485-493`) calls `bb_append` *before* `bb_push` and never
    revisits the record. `published` lives only in the returned dict.
  - `doctor` says **nothing** about an unpublished lease.
  **The read failure is the severe half and is never stated.** The message names
  the *write* it noticed ("not published"). The failure that actually invalidates
  the grant is the **fetch** — `bb_snapshot` could not read peers' leases, so
  `bb_conflicts` ran against an incomplete set. socom reports the symptom it saw
  and stays silent about the one that makes the answer wrong.
  **Second surface, same defect, measured:** `attest` on an unreachable remote
  prints `recorded [f-…] against src/other.py (verified)` — a durable quality
  tier — while the peer session's `socom findings src/other.py` returns
  **`0 outstanding`**. A finding nobody can read is stamped `verified`.
  **Third surface — the one that matters most:** the MCP front-end
  (`mcp.py:218`) returns `bb_do_claim`'s dict verbatim with
  `isError = not out["ok"]`. `ok` is `True`, so a local-only claim reaches an
  agent as **`granted: true`, no error**, with `published: false` buried among
  the fields. Agents are the blackboard's intended users and get the weakest
  signal of the three front-ends.
  **Why this is not pre-exposure P0** despite the severity: it cannot fire at
  `n=1` — it needs two concurrent sessions. It does not compete with
  [[EV-NONAUTHOR-EXPOSURE-01]].
  ⚠️ **It does invalidate the Phase 3a blackboard trial's instrument.** That
  trial's stated setting is *"three or more people running concurrent agents on a
  shared repo"* — precisely the configuration in which this fires. A trial that
  tallies zero category-A saves cannot distinguish "the thesis is wrong" from
  "some participant's remote was refusing and their leases were never visible."
  Repair this **before** Phase 3a runs in its real setting, or the tally is
  uninterpretable — the same disarmed-kill-criterion shape decision
  [`0001`](../decisions/0001-exposure-before-capability.md) already identified.
  **Falsifiable acceptance:** re-run the A/B; in the variable run either the
  grant is refused, or it is granted with a durable marker on the record that
  `--scan`, `doctor` and the MCP response all surface — and the **fetch** failure
  is named distinctly from the push failure. **Files:**
  `src/socom/blackboard.py` (`bb_do_claim`, `bb_do_attest`, `bb_snapshot`,
  `bb_push`), `src/socom/mcp.py`.

- `DEF-UNRESOLVABLE-GATE-LEAVES-NO-TRACE-01` **READY P1** — **When a gate cannot
  run at all, socom records nothing — so a repo whose `core.hooksPath` still
  declares socom's gates can commit ungated indefinitely, and no socom surface
  can ever say so.** The class: *enforcement whose declaration is durable, whose
  capability is resolved through a referent socom does not own, and whose
  resolution failure degrades open without leaving a trace.*
  **MEASURED (n=1 controlled A/B, throwaway repo, 2026-08-05, `caa677a`).**
  Same repo, same bound-and-failing `checks.medium`, one variable — whether the
  binary resolves:
  - **A, reachable:** `pre-commit: AMBER — failed (rc=1); breach logged`;
    `.socom/gates/breaches.log` 2 → 4 lines. Visible to `socom breach`.
  - **B, unreachable** (the downloaded file deleted; symlink AND `socom.binpath`
    both dangle — `install` symlinks at the file you ran and `adopt` records that
    same path, so the two resolution tiers die together): commit proceeds,
    `breaches.log` **4 → 4**, `find .socom -newermt '-20 seconds'` returns
    **nothing**. One stderr line, and `core.hooksPath` still reads `.githooks`.
  - **C, detector:** with socom restored, `doctor` prints 5 findings — compiled-view
    drift and unbound checks — and **nothing** about the three commits that had
    just gone through ungated.
  **The generative structure, and why C is not an oversight:** every detector
  socom has (`doctor`, `value`, `gate session-start`) runs *inside* socom, so
  socom's own unreachability is the one condition they structurally cannot
  observe. The contrast proves the class boundary is real: drift in an **owned**
  referent (compiled views vs `canonical_hash`) is caught and exits P0; the
  reachability of the binary — an **unowned** referent — is caught by nothing.
  **Not the fail-open.** Fail-open-locally is deliberate doctrine
  (`canon/residuality.xml` `fail-safe-defaults` + `psychological-acceptability`,
  the published-gate model). What it fails is that same file's
  **`compromise-recording`** — *"a detectable breach beats a silent one. **Fail
  it when a fail-open path leaves no trace.**"* socom names this exact class in
  its own constitution and the code fails the principle it wrote.
  **socom already handles this class correctly elsewhere**, which is why this
  reads as an inconsistency rather than a philosophy: `spawn --exec` resolves the
  same *kind* of unowned referent (a runtime binary on PATH) and exits **loudly**
  (`spawn.py:413`, "R6: degrade loudly"), with a preflight that surfaces it at
  onboarding (`install.py:200`). The precedent exists; the hook path predates it.
  **Class sweep — three instances, one detected:**
  | Instance | Site | Degrade | Detector |
  |---|---|---|---|
  | binary unreachable | `HOOK_RESOLVER` → `exit 0` | stderr only | **none, and none possible in-process** |
  | `checks.*` unbound | `gate.py:297` *"unbound — passing"* | returns, **no `log_breach`** | partial — `doctor`/`value` warn |
  | `uninstall` without `unadopt` | `install.py` prints a NOTE | every adopted repo ungated | none |
  Note `gate.py:297` against `gate.py:312`: a check that **fails** is recorded;
  a check that **cannot run** is not. The breach ledger records exactly one of
  three outcomes.
  **Relation to [[DEF-STATUS-CLAIMS-UNLABELLED-01]] — adjacent, not duplicate.**
  That row's second instance shows RED paths (`sys.exit`) recording nothing, so
  `breaches.log` cannot contain a *stopped* slip. This row is the third
  population: gates that were never *assessed at all*. Together: of {blocked,
  proceeded-after-assessment, never-assessed}, only the middle is recorded.
  **Why P1, not P0.** It needs time to materialize — the file must be moved or
  cleaned *after* install — so a single pilot session will not hit it. It does
  not compete with [[EV-NONAUTHOR-EXPOSURE-01]] and is not an argument to delay
  it. Found by reading, not by exposure.
  ⚠️ **Do not "fix" this by swapping the symlink for a copy** — that is the
  instance, not the class; PATH can break from a login-shell reorder, an
  `uninstall`, or a moved checkout with no symlink involved. ⚠️ **Do not fail
  closed** — a hook that blocks because socom is missing is the exact shape
  `psychological-acceptability` says gets `--no-verify`'d permanently.
  ⚠️ The stderr line asserts *"CI re-asserts"*; nothing verifies that the repo
  **has** CI. In the repro it did not.
  **Falsifiable acceptance:** re-run the A/B above; in run B, a socom surface
  names the ungated invocations — count and time window — after the binary
  returns. Blocked on a spiked fix mechanism, see
  [`decisions/0002`](../decisions/0002-unresolvable-enforcement-must-record.md).
  **Files:** `src/socom/gate.py` (`HOOK_RESOLVER`, `:297`), `src/socom/install.py`,
  `src/socom/lifecycle.py`.

- `DEF-STATUS-CLAIMS-UNLABELLED-01` **READY P1** — **socom derives a
  `verified`/`asserted` tier for every finding an agent records, and applies that
  discipline to nothing it says about itself.** VERIFIED at
  `src/socom/blackboard.py:508`: `"tier": "verified" if evidence else "asserted"`,
  with a comment citing arXiv 2310.01798 (ICLR 2024) on why self-declared
  verification degrades behaviour. Every status socom emits about its own state is
  **unlabelled**, so an asserted claim renders identically to a verified one.
  Seven surfaces, all found independently by the cohort: the quickstart bind
  checkmark (*"gates now run YOUR tests"*, written without executing the command —
  5/5 hit this); the CI step's name; `socom value`; `socom doctor`; `socom precond`;
  `knowledge N chunks`; the adoption bar.
  The sharpest instance, VERIFIED: T5's own message says *"run `socom embed &&
  socom eval` — **L1 must beat the recorded floor before it serves**"*, and then
  T6 "operational (L1 retrieval live)" fires on `vectors.json` **existing**
  (`lifecycle.py:625`). `eval.json` carries a real `passed` boolean and is never
  read. socom states the requirement and checks for a file.
  Second instance, VERIFIED: `value.py:_val_gate_catches` counts lines of
  `breaches.log` and prints *"slips stopped before they landed"* — but every
  `log_breach` call site sits on an AMBER path that **proceeds**
  (`gate.py:117,130,201,233`), and every RED is a bare `sys.exit` recording
  nothing. The log **structurally cannot contain a stopped slip**; the metric
  counts exactly the population that was not stopped.
  ⚠️ **Scope here is labelling only** — each surface states what it derived its
  claim from. Changing what they derive *from* is [[SUBSTRATE-STATUS-TIER-SWEEP-01]],
  BLOCKED. This keeps `doctor`/`precond`'s deliberate static/fast charter
  (`lifecycle.py:459`) intact while making what they print true.
  ⚠️ **P1, and deliberately not repaired before exposure:** `PILOT.md`'s report
  list asks *"did a metric mislead you?"* — this is a finding the five participants
  are supposed to generate. Repairing it first deletes the finding, per decision
  0001 §Amendment 1 rule 3.
  **Falsifiable acceptance:** each of the seven surfaces either derives its claim
  from an execution record or states that it is reporting presence.
  **Files:** `src/socom/{value,lifecycle,install}.py`.

## Done

The four P0 rows above. No P1 row has been worked, deliberately — see the P1
section's own reasons, and decision 0001 §Amendment 1 rule 3 for
`DEF-STATUS-CLAIMS-UNLABELLED-01` in particular.

---

## Note

This bucket exists because a defect repair was neither a capability nor a fact
about the world, and so had no legitimate row shape — see decision 0001
§Amendment 1. Its `P0` section is capped at four rows on purpose: those are the
defects a stranger hits before their session ends, and repairing them is what
stops [[EV-NONAUTHOR-EXPOSURE-01]] from spending a scarce participant on
something already written down here.

**A full defect backlog is not progress toward the D-tier.** Rows here repair a
tool nobody outside this repo has yet chosen to use.
