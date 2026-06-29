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
  judge    calibrate a model assessor against human labels: confusion matrix +
           TPR/TNR/precision over a labelled set (.socom/evals/<set>.jsonl);
           --gate blocks unless BOTH TPR & TNR meet the threshold (Phase 2b)
  lesson   experience -> durable retrievable rules: candidates (from cycle
           hotspots) | list | promote | retire (preserved, never deleted)
  precond  is THIS work ready? fast pre-flight [seat]; auto-heals safe gaps,
           warns by default, blocks only the unrecoverable; --no-heal for CI
  introspect post-session self-capture: handoff evidence -> replayable
           assertion log (+ lesson candidates from captured failures), no model
  contract make the contract testable: verify runs a contract's <check> <run>
           commands (PASS/FAIL on exit), flags no-run checks MANUAL; --record
           appends the outcome to the run ledger (cycle data) | show |
           adequacy (is a GREEN verify real? flags no/trivial checks, missing
           regression-surface; --gate blocks on a strong weakness — Phase 2c)
  context  context as a first-class artifact: verify a context envelope (or
           .socom/context/) is schema-valid, within budget, and (CTX-2) its
           declared input_tokens match a re-measure of the <inputs> refs | show |
           measure (write counts from the live refs) | compress (drop the
           lowest-relevance inputs until within budget)
  value    first-run value readout: gate catches, scored runs, context
           adherence, claims, knowledge, adoption rung — signals already on
           disk, no new instrumentation (the why, made legible)
  spawn    launch a worker into a seat against a promise: forge the dispatch
           brief (verbatim -> envelope -> contract) + a run record; default
           prints the launch cmd, --exec background-launches. Never writes a verdict
  monarch  reconcile-and-reap supervisor over run records (no daemon): tally
           liveness | reap dead-but-running (one amber breach) | recover
           re-dispatches dead-but-unkept under a cap | triage ranks by recovery-worth
  trace    export the run registry + ledger as OpenTelemetry GenAI spans
           (OTLP/JSON) for any trace tool; --stdout streams, default writes
           .socom/traces/ — replayable observability (Phase 2a)
  forge    domain verbs (canon forge.xml) bound to this repo's commands —
           `forge list` shows verbs + bindings (the repo-specific action layer)
  greet    adoption-ladder greeting — where you are, what's next
  statusline Claude Code statusLine: adoption bar + context-consumption meter
           (reads the host's statusline JSON on stdin; GSD-style ctx meter)
  quickstart one command from a fresh repo to a live substrate: adopt + auto-bind
           gates to your real test command + build the retrieval floor/index +
           runtime preflight, ending on a `value` readout (the brand-new-user on-ramp)
  adopt    one-shot: plant + compile + wire git hooks (fresh clone -> live gates)
  install  symlink this checkout onto PATH (~/.local/bin) so `socom` just works
  uninstall remove the socom symlink (only if it points at this checkout)

All intelligence is canonical (.socom/); compiled views are one-way renders
carrying a source hash (residue R3). Local gates may be bypassed for flow;
CI re-asserts them (residue R1).
"""
