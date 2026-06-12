# Runtime Adapters

Thin, one-way compilers from the canonical store (`.socom/`) to each
participant's native dialect. All intelligence stays canonical; an adapter
only renders. Every compiled file carries a `generated — do not edit` header
with the hash of its canonical source; the session-start gate treats hash
mismatch as P0 drift.

| Adapter | Renders |
|---|---|
| `claude-code` | `CLAUDE.md` (constitution + repo bindings), `.claude/agents/<seat>.md`, `.claude/skills/<procedure>/`, hooks wired to gates (`SessionStart`/`TaskCompleted`/`Stop`), memory hydration into `~/.claude/projects/<slug>/memory/` |
| `codex` / generic agent | `AGENTS.md` |
| `cursor` | `.cursor/rules` |
| `human` | `CONTRIBUTING.md` view + onboarding doc, generated from constitution, roles, and gates (residue R13 — the substrate explains itself) |
| `git` (always on) | `pre-commit` / `pre-push` hooks running the repo's bound checks + commit-format contract |
| `ci` (always on) | Pipeline jobs re-asserting every gate (residue R1 — the incorruptible floor) |

The `git` and `ci` adapters are the enforcement floor every participant hits,
including humans and hook-less runtimes. Losing any other runtime loses an
accelerator, never enforcement.
