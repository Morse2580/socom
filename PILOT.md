# SOCOM pilot guide — start testing in 5 minutes

**Status: v0.1 — a supervised pilot, not production.** You are stress-testing the
*human residues* (does a gate annoy you into bypassing it? does a metric mislead
you?), not a finished product. That is the point. The fastest way to make SOCOM
real is to run it on one repo you care about and report where it lied or got in
your way.

This guide is written so you can read it yourself **or** paste it to Claude Code and
say *"walk me through this on this repo"* — see [With Claude Code](#with-claude-code).

---

## Is it safe? (read this first)

**Yes, for a supervised pilot on one repo.** Concretely:

- SOCOM is **additive and non-destructive**: it plants files (never clobbers your
  edits), wires git hooks that run *your own* commands, and builds an index. It does
  **not** delete your code, does **not** auto-push, and does **not** run any AI worker
  unless you explicitly pass `--exec`.
- It **degrades loudly**: when it can't do something honestly (detect your test
  command, certify retrieval), it says so and stops — it never fabricates.

**Three things to keep OFF / not trust during the pilot** (we're telling you because
the tool's own audit did):

1. **Leave `spawn --exec` and `monarch recover --exec` OFF.** The auto-orchestration
   loop has not been validated in production yet. Use `spawn` in its default
   (print-the-command) mode only.
2. **Treat the metrics (`value`, `cycle`, trust) as advisory.** The ledger is a plain
   file; the numbers are not yet tamper-evident.
3. **`pre-commit` is a *warning* (amber), not a block.** Only `pre-push` and CI
   actually stop you.

Everything else in the 5-minute path below is safe to run on a real repo.

---

## The 5-minute path

```sh
# 1. Get the tool (one self-contained file — read it, it's plain Python)
curl -fsSLO https://raw.githubusercontent.com/Morse2580/socom/main/bin/socom
chmod +x socom && ./socom install        # symlinks onto ~/.local/bin, no sudo

# 2. In a repo you care about, climb the whole on-ramp in one command
cd ~/your-repo
socom quickstart
```

`quickstart` will:
- plant the substrate + wire git hooks,
- **auto-bind your gate checks to your real test command** (Make / npm / pytest /
  cargo / go) — or tell you exactly what to edit if it can't detect one,
- build a knowledge index and **answer a question from canon live** so you see
  retrieval work,
- check whether your AI runtime is ready,
- end on a `value` readout and your adoption rung.

If it stalls at **T2 ("checks unbound")**, that's honest — it found no test command
and refused to invent one. Bind it yourself and re-run:

```sh
# example: a Terraform repo
#   edit socom.yaml -> checks.fast: "terraform -chdir=infra fmt -check -recursive"
socom compile
socom gate fast        # now runs YOUR check — watch it catch real issues
```

That's the core loop. A bound gate that catches something real (a failing test, a
formatting drift) and then goes green after you fix it — **that is the value.**

---

## What to actually test (and what to skip)

| Try this | What it proves |
|---|---|
| `socom quickstart` on 2–3 different repos (one with tests, one without) | the on-ramp + the honest degrade |
| Bind a real check, break it, run `socom gate fast` | a gate catching a real slip |
| `socom query "how do I ..."` | retrieval over canon (works at L0 immediately) |
| `socom contract verify <promise.xml>` | falsifiable done-ness on a real contract |
| `socom value` / `socom greet` | where you are on the adoption ladder |
| **Skip for now:** `spawn --exec`, `monarch recover --exec` | not pilot-ready |

---

## What to report back (this is the actual experiment)

The residuality model says the failure modes are *human*, not code. So watch yourself,
and tell us:

- **Did you reach for `git commit --no-verify`?** When, and why? (a gate too slow, a
  false positive, deadline panic — all valuable)
- **Did a gate fire a FALSE POSITIVE?** Even one on a bad day kills adoption — we need it.
- **Did a metric mislead you** — did `value`/`cycle` say something you didn't trust?
- **Where did discovery stall?** What did you have to read the source to understand?
- **Did you "game" a gate** (satisfy the check without doing the work)? Be honest — that
  tells us the gate is theater.

File these as GitHub issues, or just paste them back. Negative findings are the most
useful: a tester who bypassed a gate teaches more than one who didn't.

---

## With Claude Code

SOCOM is built for Claude Code. After `socom quickstart`, your repo has a generated
`CLAUDE.md` and `.claude/agents/` — Claude Code reads them automatically. To make
discovery effortless, open the repo in Claude Code and paste:

> Read CLAUDE.md and AGENTS.md, then give me a 5-line tour of what SOCOM set up in
> this repo. Then: pick one real check I should bind for this codebase, bind it in
> socom.yaml, run `socom compile`, and run `socom gate fast` so I can see it work.
> Do not touch `spawn --exec` or `monarch`. Explain each step as you go.

Claude Code will discover the substrate, bind a real gate, and demonstrate a catch —
the whole 5-minute path, guided. Ask it follow-ups like *"what does the residuality
gate check?"* or *"show me what `value` is measuring and whether I should trust it."*

---

## The honest bottom line

You are piloting a **mature substrate** (gates, contracts, residuality, retrieval) that
already catches real bugs, wrapped around an **unproven orchestration layer** we're
asking you to leave off. Test the substrate hard, report where it annoyed or misled
you, and you'll be stressing exactly the residues that decide whether v0.1 graduates.
