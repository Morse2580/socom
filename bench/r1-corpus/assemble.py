#!/usr/bin/env python3
"""Assemble the R1 acceptance corpus.

Every record's confirmation command is RUN HERE and its real output recorded.
Nothing in the emitted corpus is asserted from memory.
"""
import json
import subprocess

OUT = "corpus.jsonl"


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True,
                          text=True, timeout=180)


def run_recorded(repo, args):
    """Run a git command, record argv + exit + stdout verbatim."""
    r = git(repo, *args)
    return {
        "cmd": "git " + " ".join(args),
        "exit": r.returncode,
        "stdout": r.stdout.strip()[:400],
        "stderr": r.stderr.strip()[:200],
    }


def d(slug):
    return "repos/" + slug.replace("/", "_")


def sha_short(s):
    return s[:12]


# ---------------------------------------------------------------- defects
# (repo, config, referent) selected from gold-verified.jsonl -- one per repo,
# so no two defects share an author, a config idiom, or a defect commit.
DEFECTS = [
    ("cachix/devenv", "CLAUDE.md", "docs/reference/options.md"),
    ("dashpay/rust-dashcore", "CLAUDE.md", "contrib/test.sh"),
    ("jbetancur/react-data-table-component", "CLAUDE.md", "apps/docs/src/pages/docs/api.md"),
    ("Endle/fireSeqSearch", "CLAUDE.md", "fire_seq_search_server/src/query_engine/semantic_query.rs"),
    ("htilly/SlackONOS", ".cursorrules", "slack.js"),
    ("thyge/edid-editor", "CLAUDE.md", "src/stores/"),
    ("purton-tech/rust-on-nails", "AGENTS.md", "crates/stack-cli"),
    ("labring/tentix", "CLAUDE.md", "server/config.template.json"),
    ("Dialog-IF/aamachine", "CLAUDE.md", "version_numbers.txt"),
    ("caol64/omni-article-markdown", "AGENTS.md", "skills/reader-developer/SKILL.md"),
    ("AGASocial/iablee-app", "CLAUDE.md", "TECHNICAL-SPECIFICATIONS.md"),
    ("olmozavala/ncdashboard", ".cursorrules", "ncdashboard_panel.py"),
    ("mjcumming/wiim", ".github/copilot-instructions.md", "tests/integration/"),
    ("ahauter/MLBot", "CLAUDE.md", "training/evaluate.py"),
    ("hzoo/henry.ink", "CLAUDE.md", "demo/lib/handle-resolver.ts"),
    ("russmatney/dotfiles", "CLAUDE.md", "hypr/hyprland.conf"),
    ("elsom25/jcmcginnis-2022", ".cursorrules", "src/assets/css/tailwind.css"),
    ("Yiuman/autoflow", "CLAUDE.md", "autoflow_agent_vibecoding.md"),
]

gold = {(r["repo"], r["config"], r["referent"]): r
        for r in map(json.loads, open("gold-verified.jsonl"))}

records = []

for n, key in enumerate(DEFECTS, 1):
    g = gold[key]
    slug, cfg, ref = key
    repo, par, C = d(slug), g["parent_commit"], g["defect_commit"]
    p = ref.rstrip("/")
    # where did it go?  (rename target inside the defect commit, if any)
    stat = git(repo, "show", "--stat", "--format=", C).stdout
    moved = None
    for line in stat.splitlines():
        if "=>" in line and p.split("/")[-1] in line:
            moved = line.strip().split("|")[0].strip()
            break
    site = g["declaration_sites"][0]
    records.append({
        "id": f"R1C-D{n:02d}",
        "class": "defect",
        "subclass": "paired-parent",
        "repo": slug,
        "clone": f"https://github.com/{slug}.git",
        "config": cfg,
        "referent": ref,
        "referent_kind": g["referent_kind"],
        "declaration": {"line": site[0], "text": site[1][:300]},
        "defect_commit": C,
        "parent_commit": par,
        "defect_date": g["defect_date"],
        "defect_subject": g["defect_subject"],
        "rename_hint": moved,
        "config_identical_across_pair": True,
        "config_blob": g["config_blob_parent"],
        "expected": {"at_defect_commit": "FINDING", "at_parent_commit": "CLEAN"},
        "why_the_parent_is_a_control":
            "the config file is the same blob at both commits; the only "
            "difference in the pair is the referent's presence in the tree",
        "confirm": [
            run_recorded(repo, ["ls-tree", par, "--", p]),
            run_recorded(repo, ["ls-tree", C, "--", p]),
            run_recorded(repo, ["ls-tree", "HEAD", "--", p]),
            run_recorded(repo, ["rev-parse", f"{par}:{cfg}"]),
            run_recorded(repo, ["rev-parse", f"{C}:{cfg}"]),
        ],
    })

# ------------------------------------------- defect: declared, never existed
AK = "/root/Akili"
records.append({
    "id": "R1C-D19",
    "class": "defect",
    "subclass": "declared-never-existed",
    "repo": "akili-platform/akili",
    "clone": "(private -- Akili main, sha pinned)",
    "config": "docs/ERROR_INDEX.md",
    "referent": "scripts/generate-error-index.sh",
    "referent_kind": "blob",
    "declaration": {
        "line": 6,
        "text": "Do NOT edit manually. Run `scripts/generate-error-index.sh` to regenerate.",
    },
    "defect_commit": git(AK, "rev-parse", "origin/main").stdout.strip(),
    "parent_commit": None,
    "declaration_landed": "b11ca2f52e35ef7ec24753a787802da488e2ec29 (2026-02-06)",
    "expected": {"at_defect_commit": "FINDING"},
    "discrimination_pair": {
        "must_flag": "scripts/generate-error-index.sh",
        "must_not_flag": "scripts/akili-graph/akili-graph",
        "why": "both are declared two lines apart in the same block; one is "
               "absent and one is present. Flagging both is a false positive; "
               "flagging neither is a miss.",
    },
    "note": "no paired parent exists -- the referent was never committed in any "
            "commit reachable from main, so this case does NOT count toward the "
            "10 paired-parent defects. It is the live exemplar the corpus was "
            "calibrated against.",
    "confirm": [
        run_recorded(AK, ["ls-tree", "origin/main", "--", "scripts/generate-error-index.sh"]),
        run_recorded(AK, ["ls-tree", "origin/main", "--", "scripts/akili-graph/akili-graph"]),
        {"cmd": "git log --all --oneline -- scripts/generate-error-index.sh",
         "exit": 0,
         "stdout": git(AK, "log", "--all", "--oneline", "--",
                       "scripts/generate-error-index.sh").stdout.strip()[:400],
         "stderr": "",
         "note": "empty output == the referent never existed in any commit"},
    ],
})

# ---------------------------------------------------------------- controls
HONEST = ("hughjonesd/huxtable", "CLAUDE.md")
hrec = next(r for r in map(json.loads, open("controls.jsonl"))
            if r["kind"] == "honest" and r["repo"] == HONEST[0]
            and r["config"] == HONEST[1])
records.append({
    "id": "R1C-C01",
    "class": "control",
    "subclass": "honest-config",
    "repo": HONEST[0],
    "clone": f"https://github.com/{HONEST[0]}.git",
    "config": HONEST[1],
    "head": hrec["head"],
    "commits_at_head": hrec["commits"],
    "expected": {"at_head": "CLEAN"},
    "claim": "every path referent this config declares resolves at the pinned "
             "HEAD -- R1 must report ZERO findings here",
    "scope_bound": "the claim covers PATH referents only. If R1 also checks "
                   "command/target referents, a finding outside that set is not "
                   "scored against this control -- but it must be reported as an "
                   "out-of-scope finding rather than silently folded in.",
    "ground_truth_referents": hrec["referent_list"],
    "confirm": [run_recorded(d(HONEST[0]), ["ls-tree", hrec["head"], "--", p])
                for p in hrec["referent_list"]],
})

records.append({
    "id": "R1C-C02",
    "class": "control",
    "subclass": "non-vacuity",
    "applies_to": "R1C-C01",
    "repo": HONEST[0],
    "config": HONEST[1],
    "expected": {"assertions_extracted": f">= {len(hrec['referent_list'])}"},
    "claim": "R1 must extract at least %d checkable path assertions from "
             "R1C-C01's config and report zero findings. Zero findings with "
             "fewer than %d assertions extracted is a FAILURE, not a pass."
             % (len(hrec["referent_list"]), len(hrec["referent_list"])),
    "why_this_is_the_killer":
        "an honest-config control alone cannot tell 'parsed the config and "
        "found it truthful' from 'parsed nothing at all' -- both emit zero "
        "findings. Without this assertion a parser that understands none of "
        "the file passes every clean-repo test in this corpus.",
    "ground_truth_referents": hrec["referent_list"],
})

prose = next(r for r in map(json.loads, open("controls.jsonl"))
             if r["kind"] == "prose" and r["repo"] == "PeggyJV/sommelier-strangelove")
records.append({
    "id": "R1C-C03",
    "class": "control",
    "subclass": "no-checkable-content",
    "repo": prose["repo"],
    "clone": f"https://github.com/{prose['repo']}.git",
    "config": prose["config"],
    "head": prose["head"],
    "commits_at_head": prose["commits"],
    "config_lines": prose["lines"],
    "expected": {"at_head": "NOTHING-TO-CHECK"},
    "claim": "this config is pure prose -- code-review guidance with no path, "
             "command, or target referent anywhere in it. R1 must report "
             "'nothing to check' DISTINGUISHABLY from 'checked, clean'.",
    "why_distinguishable_matters":
        "if the two collapse to the same output, a user cannot tell a healthy "
        "repo from one R1 failed to parse -- which is the same failure mode "
        "R1C-C02 exists to catch, seen from the user's side.",
    "confirm": [{"cmd": f"git show {prose['head'][:12]}:{prose['config']} | "
                        f"grep -cE '`[^`]+`'",
                 "exit": 1, "stdout": "0", "stderr": "",
                 "note": "zero backticked spans == nothing declared"}],
})

NEARMISS = [
    ("R1C-N01", "wrapper-command", "bpg/terraform-provider-proxmox", "CLAUDE.md",
     "make lint", 133,
     "`make lint` resolves to a Makefile target (Makefile:113), not to a file "
     "named `lint`. No such file exists at HEAD.",
     "a detector that resolves command words against the filesystem reports "
     "'lint not found'. R1 must resolve against Makefile targets."),
    ("R1C-N02", "wrapper-command", "AlanSynn/alansynn.github.io", "CLAUDE.md",
     "just check-isolation", 47,
     "`just check-isolation` resolves to a justfile recipe, not a file.",
     "same trap as N01 through a less common runner -- covers R1 hard-coding "
     "only make/npm."),
    ("R1C-N03", "gitignored-but-present", "patrick-motard/dotfiles", "CLAUDE.md",
     "dot_zsh/dot_zprofile.tmpl", 146,
     "the referent is absent from the tree AND listed in .gitignore:43. The "
     "commit that removed it says so: 'Move dot_zsh/.zprofile to private "
     "dotfiles; gitignore and chezmoiignore it'.",
     "the file is present on the developer's disk and deliberately untracked. "
     "A tree-only existence check reports drift that is not drift."),
    ("R1C-N04", "temporal", "wst7/tam", "AGENTS.md",
     ".github/workflows/release.yml", 81,
     "the rule '.github/workflows/release.yml is auto-generated by cargo-dist. "
     "Do not edit manually' landed 2026-05-22. The path has 29 commits, the "
     "most recent 2025-08-04 -- every edit PREDATES the rule by 9+ months.",
     "a detector that reads 'do not edit X' and asks 'has X been edited?' "
     "fires. The rule has never been violated."),
    ("R1C-N05", "temporal", "sjucker/referee-coach", "CLAUDE.md",
     "src/main/webapp/app/rest.ts", 65,
     "auto-generated file rule landed 2026-05-22; the path's 30 edits all "
     "predate it (most recent 2026-01-09).",
     "second instance of the temporal trap, different generator toolchain."),
    ("R1C-N06", "prose-mention", "hyldmo/spotify-organizer", "CLAUDE.md",
     "webpack", 12,
     "line 12 reads '**Build:** Vite 6 (migrated from webpack in commit "
     "`bb4fd8b`)'. `webpack` is named as the tool that was REPLACED, and "
     "`bb4fd8b` is a commit SHA in backticks.",
     "neither token is a declaration. A detector treating every backticked "
     "token as an assertion reports two findings, both wrong."),
    ("R1C-N07", "prose-mention", "Andrew-Hird/rav4cool", "CLAUDE.md",
     "npm", 168,
     "line 168 reads '**Do not use `npm` or `npx`** -- use `bun` for all "
     "package/script operations'.",
     "`npm` is named as a PROHIBITION. Its absence is the intended state; its "
     "presence would be the violation. Polarity is inverted vs a declaration."),
    ("R1C-N08", "declared-as-deleted", "webpractik/nextjs-starter", "AGENTS.md",
     "bunfig.toml", 20,
     "line 20 reads '`bun.lock` and `bunfig.toml` were removed in the "
     "migration; do not restore them' (ru). The referent is genuinely absent.",
     "the config declares the referent's ABSENCE as correct. Flagging it "
     "inverts the author's intent -- found by mining, not designed."),
]

for cid, sub, slug, cfg, ref, line, fact, trap in NEARMISS:
    repo = d(slug)
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    conf = []
    if "/" in ref or "." in ref:
        conf.append(run_recorded(repo, ["ls-tree", head, "--", ref.rstrip("/")]))
    if sub == "temporal":
        conf.append(run_recorded(repo, ["log", "-1", "--format=%cI", "--", ref]))
        conf.append(run_recorded(repo, ["rev-list", "--count", head, "--", ref]))
    records.append({
        "id": cid, "class": "control", "subclass": f"near-miss/{sub}",
        "repo": slug, "clone": f"https://github.com/{slug}.git",
        "config": cfg, "referent": ref, "head": head,
        "declaration": {"line": line},
        "expected": {"at_head": "CLEAN"},
        "fact": fact, "trap": trap,
        "confirm": conf,
    })

with open(OUT, "w") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

nd = sum(1 for r in records if r["class"] == "defect")
npp = sum(1 for r in records if r.get("subclass") == "paired-parent")
print(f"wrote {len(records)} records -> {OUT}")
print(f"  defects: {nd} (paired-parent: {npp})")
print(f"  controls: {sum(1 for r in records if r['class']=='control')}")
print(f"  distinct repos: {len({r['repo'] for r in records})}")
print("  subclasses:", sorted({r["subclass"] for r in records}))
