"""socom — substrate for orchestrated, contract-bound machines.

Commands:
  init     plant the substrate into a repo (.socom/ + socom.yaml)
  compile  render canonical store -> runtime adapters (CLAUDE.md, AGENTS.md,
           .cursor/rules, .claude/agents/, .githooks/)
  doctor   detect drift between canonical and compiled views; config health
  gate     run a gate by id with band semantics (amber warns+logs, red blocks);
           `gate task-completion <promise.xml>` also records its verdict to the
           run ledger (cycle data) — no promise arg, no row
  hydrate  copy repo memories into the Claude Code project memory dir
  index    emit (id, text, metadata) chunks from embed="true" elements (L1 RAG)
  claim    acquire a domain claim (TTL auto-expiry); --scan to list (R2)
  release  release a domain claim (<domain> or --all)
  handoff  generate a handoff skeleton from git state; fill before closeout
  prompt   generate next-session prompt from latest handoff, claim-verified
  breach   list/resolve amber breaches — the loop amber must close (HR3)
  baseline measure the L0 retrieval floor; plants probes.yaml (the L1 contract)
  embed    build the L1 index (BM25, stdlib, offline) from the redacted registry
  query    ask the substrate a question; L1 with loud L0 fallback (R6)
  eval     L1 acceptance gate: beats the floor on the probes or exits RED
  cycle    roll the run ledger into a scored cycle: pass@1/pass@k by seat,
           hotspots; --gate --threshold N for the pass-rate gate (R: evals)
  lesson   experience -> durable retrievable rules: candidates (from cycle
           hotspots) | list | promote | retire (preserved, never deleted)
  precond  is THIS work ready? fast pre-flight [seat]; auto-heals safe gaps,
           warns by default, blocks only the unrecoverable; --no-heal for CI
  introspect post-session self-capture: handoff evidence -> replayable
           assertion log (+ lesson candidates from captured failures), no model
  contract make the contract testable: verify runs a contract's <check> <run>
           commands (PASS/FAIL on exit), flags no-run checks MANUAL; --record
           appends the outcome to the run ledger (cycle data) | show
  context  context as a first-class artifact: verify a context envelope (or
           .socom/context/) is schema-valid, within budget, and (CTX-2) its
           declared input_tokens match a re-measure of the <inputs> refs | show |
           measure (write counts from the live refs) | compress (drop the
           lowest-relevance inputs until within budget)
  greet    adoption-ladder greeting — where you are, what's next
  statusline Claude Code statusLine: adoption bar + context-consumption meter
           (reads the host's statusline JSON on stdin; GSD-style ctx meter)
  adopt    one-shot: plant + compile + wire git hooks (fresh clone -> live gates)
  install  symlink this checkout onto PATH (~/.local/bin) so `socom` just works
  uninstall remove the socom symlink (only if it points at this checkout)

All intelligence is canonical (.socom/); compiled views are one-way renders
carrying a source hash (residue R3). Local gates may be bypassed for flow;
CI re-asserts them (residue R1).
"""
