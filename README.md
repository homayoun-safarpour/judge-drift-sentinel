# judge-drift-sentinel

**Your LLM-judge eval score dropped after a provider model update—not because your system regressed. `drift-sentinel check` tells you in one command whether the movement is real, judge drift, or noise, using a frozen human-labeled anchor set (no extra model calls).**

[![CI](https://github.com/homayoun-safarpour/judge-drift-sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/homayoun-safarpour/judge-drift-sentinel/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## The problem

Teams that grade LLM systems with an LLM judge get a moving scoreboard and cannot tell why it moved:

| What moved | What it looks like | What teams do (wrongly) |
|---|---|---|
| The system | Eval score drops after a deploy | Roll back (correct only if it really was the system) |
| The judge model | Provider ships a silent update behind `-latest` | Roll back a healthy deploy, or chase a phantom regression |
| The judge prompt | Someone edited one rubric sentence in week 8 | Trust week-1 vs week-9 charts that are not comparable |
| Nothing | Ordinary judge variance | Re-run until the number looks right |

All four produce the same dashboard artifact: a number that moved. The score alone cannot tell you which one happened. You need a second measurement that isolates the judge.

## The insight

Freeze a small set of human-labeled examples. The humans never change, so any change in the judge's agreement with them can only come from the judge:

```
                     frozen anchor set (human labels, never changes)
                                       |
        baseline run:  judge scores anchors  ->  kappa vs humans = 0.83
        current  run:  judge scores anchors  ->  kappa vs humans = ?
                                       |
              +------------------------+------------------------+
              | kappa fell             | kappa held,             | both held
              |                        | live metric moved       |
              v                        v                         v
        JUDGE_DRIFT             SYSTEM_CHANGE                 STABLE
     (distrust the number)   (the movement is real)      (carry on)
```

The verdict is deterministic, computed from score files you already have, and needs zero LLM calls. It runs in CI in milliseconds.

## Install

```bash
pip install judge-drift-sentinel
```

Import package: `driftsentinel`. CLI: `drift-sentinel`.

From source (contributors):

```bash
git clone https://github.com/homayoun-safarpour/judge-drift-sentinel
cd judge-drift-sentinel
pip install -e ".[dev]"
```

Release notes and maintainer upload steps: [docs/PUBLISH.md](docs/PUBLISH.md).

## Quickstart

Label 10â€“50 representative outputs once, by hand. That file is your anchor set (JSONL):

```json
{"id": "a01", "input": "Agent answer that cites both retrieved sources correctly", "label": "pass"}
{"id": "a07", "input": "Confident answer with one fabricated citation among real ones", "label": "fail"}
```

Every time you run your eval suite, have the judge also re-score the anchors, and save one small JSON per run:

```json
{
  "judge": { "model": "frontier-4-2026-05-01", "prompt_sha": "9f2c1a" },
  "created": "2026-07-06",
  "live_metric": 0.81,
  "anchor_scores": { "a01": "pass", "a07": "pass", "...": "..." }
}
```

Pin your July run as the frozen baseline (records the anchor `freeze_hash` + kappa):

```bash
drift-sentinel baseline --anchors anchors.jsonl --run run_july.json --out baseline.json
```

Then ask the sentinel who moved:

```bash
drift-sentinel check --anchors anchors.jsonl --baseline baseline.json --current run_august.json
```

For ordinal rubrics (integer scores such as 0-3), use weighted kappa so near misses cost less than far misses:

```bash
drift-sentinel check --anchors anchors.jsonl --baseline baseline.json --current run_august.json \
  --kappa-weights quadratic --kappa-levels 0,1,2,3
```

Default `--kappa-weights none` keeps unweighted Cohen's kappa for binary pass/fail labels.

To see whether verdicts are stable or eroding across many pinned runs (not just one pair), walk the timeline:

```bash
drift-sentinel history --anchors anchors.jsonl --runs run_w1.json run_w2.json run_w3.json run_w4.json
```

Each consecutive pair gets the same 3-way verdict as `check`. If kappa falls slowly (every step under `--kappa-drop`, but the firstâ†’last window exceeds it), history flags **slow decay** (exit 2). That is the failure mode a single pairwise gate cannot see.

Exit codes make it a drop-in quality gate: `0` = STABLE (trust your numbers), `3` = SYSTEM_CHANGE (numbers are trustworthy and your system moved), `2` = JUDGE_DRIFT or slow decay (stop: the scoreboard itself is broken).

## Import from judge-reliability-kit

Do not hand-copy panel scores into sentinel files.
[judge-reliability-kit](https://github.com/homayoun-safarpour/judge-reliability-kit)
stores ratings as `{item_id: {judge_id: [label, ...]}}` (replicated labels per
judge). Sentinel documents a thin envelope (`judgekit.panel_export/v1`) that
adds the human gold map and judge fingerprint fields this tool needs:

```json
{
  "schema_version": "judgekit.panel_export/v1",
  "created": "2026-08-04",
  "live_metric": 0.81,
  "judges": {
    "gpt-4o-judge": { "model": "gpt-4o-judge", "prompt_sha": "kit-demo-01" }
  },
  "human_labels": { "a01": "pass", "a04": "fail" },
  "ratings": {
    "a01": { "gpt-4o-judge": ["pass", "pass", "pass", "pass"] },
    "a04": { "gpt-4o-judge": ["fail", "fail", "fail", "fail"] }
  }
}
```

Convert one judge's replicates into sentinel anchors + run JSON (modal =
majority vote, same rule as judgekit):

```bash
drift-sentinel import-judgekit \
  --panel examples/judgekit_panel_export.json \
  --judge gpt-4o-judge \
  --anchors-out anchors.jsonl \
  --run-out run.json
```

Bare kit ratings work too if you pass gold separately:

```bash
drift-sentinel import-judgekit \
  --panel ratings.json \
  --human-labels gold.json \
  --judge gpt-4o-judge \
  --anchors-out anchors.jsonl \
  --run-out run.json
```

Python import path: `driftsentinel.adapter.load_panel_export` â†’
`panel_to_anchors` / `panel_to_run`. Named test:
`tests/test_adapter.py::test_adapter_reads_anchor_scores_straight_from_judgekit_panel_export`.

## CI: weekly anchor re-score

Operators should not wait for a human to notice a bad ruler. This repo ships
[`.github/workflows/weekly-anchor-rescore.yml`](.github/workflows/weekly-anchor-rescore.yml):

| Trigger | What it does |
|---|---|
| Cron (Mondays 06:00 UTC) | Runs `drift-sentinel check` (or `history`) on configured paths |
| `workflow_dispatch` | Same job, with path/mode inputs you pass in the Actions UI |

**On `JUDGE_DRIFT` (exit 2):** the job opens a GitHub issue titled
`JUDGE_DRIFT: weekly anchor re-score detected judge drift` (or comments on an
existing open one), then fails so the workflow run is red. **On
`SYSTEM_CHANGE` (exit 3) or `STABLE` (exit 0):** no issue. Those are not
ruler failures.

### Wiring your own paths (no secrets in the repo)

1. Keep producing a weekly re-score JSON the same shape as `examples/run_*.json`
   (your judge scores the frozen anchors; this workflow never calls an LLM).
2. In the Actions UI â†’ **Weekly anchor re-score** â†’ **Run workflow**, set:
   - `anchors` â†’ your frozen `anchors.jsonl`
   - `baseline` â†’ pinned baseline from `drift-sentinel baseline ... --out`
   - `current` â†’ this week's re-score JSON
   - or `mode=history` + `history_runs` â†’ ordered space-separated run paths
3. For the scheduled run, either keep the defaults or edit the
   `Resolve paths` defaults in the workflow YAML to your production paths.
4. **Auth:** the workflow uses only `permissions: issues: write` and
   `secrets.GITHUB_TOKEN` (automatic). Do **not** commit PATs, OpenAI keys, or
   provider tokens. If you need issues in another repo, add a fine-scoped PAT
   as a repository secret and swap `GH_TOKEN`. Never commit the value.
5. **Smoke the drift path:** dispatch with
   `current=examples/run_current.json` (the intentional JUDGE_DRIFT fixture) and
   confirm an issue opens; then point `current` back at your real weekly file.

Named contract test:
`tests/test_weekly_rescore_workflow.py::test_weekly_rescore_workflow_opens_issue_on_judge_drift`.

## Gate for agent-loop-engine

Stack story (copy-pasteable): [agent-loop-engine](https://github.com/homayoun-safarpour/agent-loop-engine)
decides *which* backlog item is safe; this package decides whether the *eval
ruler* is still trustworthy. Before you automate either loop, fill a
[Loop Contract](https://github.com/homayoun-safarpour/agent-loop-field-guide)
(done / verifier / stop layers / state / irreversible). Wire sentinel as a `--gate NAME=COMMAND` so
**repair beats progress** when the scoreboard itself moved.

### Exit codes (raw `drift-sentinel check` / `history`)

| Verdict | Exit | Meaning |
|---|---|---|
| `STABLE` | `0` | Ruler held; live metric did not move past threshold |
| `SYSTEM_CHANGE` | `3` | Ruler held; live metric movement is real (system) |
| `JUDGE_DRIFT` (or history slow decay) | `2` | Ruler moved; do not trust the numbers |
| bad args / IO / freeze-hash mismatch | `1` | Fix the wiring before trusting any verdict |

`loop-engine` treats **only exit 0 as PASS** (see its `--gate NAME=COMMAND`
CLI). So a raw `--gate "drift=drift-sentinel check ..."` would mark
`SYSTEM_CHANGE` (exit 3) as a red gate and wrongly block feature work even
though the ruler is fine. Use the shipped remapper:

```bash
# install both CLIs, then from this repo root:
loop-engine tick --state examples/LOOP_STATE.md \
  --gate "tests=python -m pytest -q" \
  --gate "drift=python examples/as_loop_gate.py --anchors examples/anchors.jsonl --baseline examples/run_baseline.json --current examples/run_current_system.json"
```

`examples/as_loop_gate.py` forwards to `drift-sentinel check` and remaps:

| Sentinel exit | Wrapper exit | Loop effect |
|---|---|---|
| `0` STABLE | `0` | gate green |
| `3` SYSTEM_CHANGE | `0` | gate green (ruler trustworthy) |
| `2` JUDGE_DRIFT | `2` | gate red â†’ `action: repair` target `drift` |
| `1` error | `1` | gate red â†’ repair the command/paths |

Fixture paths: `run_current_system.json` â†’ wrapper exit 0 + `SYSTEM_CHANGE` in
stdout; `run_current.json` â†’ wrapper exit 2 + `JUDGE_DRIFT`. Snippet backlog:
`examples/LOOP_STATE.md`. Named tests:
`tests/test_loop_engine_gate_docs.py`.

## What is in the box

| Module | What it does | Use it when |
|---|---|---|
| `driftsentinel.anchors` | Loads the frozen anchor set, fingerprints it (`freeze_hash`) | You need proof the reference set itself never moved |
| `driftsentinel.agreement` | Cohen's kappa (unweighted) plus weighted linear/quadratic kappa for ordinal 0-3 rubrics; observed agreement; flip rate; stdlib only | You want chance-corrected agreement, including near-vs-far misses on ordinal scales |
| `driftsentinel.runs` | One judge run: model + prompt fingerprint + anchor scores | "Pin your judge" as data, not as a slogan |
| `driftsentinel.verdict` | The 3-way attribution policy, fully unit-tested | You need "who moved?", not another score |
| `driftsentinel.baseline` | Score a run and freeze it as a pinned baseline (with `anchor_freeze_hash`); `check` refuses on hash mismatch | You want a durable reference that cannot silently drift |
| `driftsentinel.history` | Verdict + kappa timeline across N runs; flags slow decay pairwise checks miss | Weekly/monthly pinned runs where erosion is gradual |
| `driftsentinel.cli` | `drift-sentinel baseline` / `check` / `history` / `import-judgekit`, plain or `--json`, gate-friendly exit codes | Wiring the verdict into CI, cron, or an agent loop |
| `driftsentinel.adapter` | Load `judgekit.panel_export/v1` (or bare ratings + gold) into `AnchorSet` / `JudgeRun` | Bridging judge-reliability-kit without hand-copying scores |
| `examples/as_loop_gate.py` | Remaps check exits so loop-engine only goes red on JUDGE_DRIFT | `--gate "drift=python examples/as_loop_gate.py ..."` |
| `.github/workflows/weekly-anchor-rescore.yml` | Weekly/manual re-score; `gh issue create` on JUDGE_DRIFT via `GITHUB_TOKEN` | Operators who need a calendar gate without a human watching CLI |

## Worked example (real output)

Freeze the July run as the pinned baseline (records the anchor freeze hash and kappa):

```
$ drift-sentinel baseline --anchors examples/anchors.jsonl --run examples/run_baseline.json --out baseline.json
pinned       : yes
anchor kappa : 0.833
freeze hash  : ca7c25804843
judge pin    : frontier-4-2026-05-01@9f2c1a
live metric  : 0.810
wrote        : baseline.json
```

The `examples/` folder ships both failure stories. In July the judge was pinned and agreed with the human labels at kappa 0.83. In August the live eval metric dropped from 0.81 to 0.66 (a 15-point fall that looks exactly like a system regression). Ask the sentinel:

```
$ drift-sentinel check --anchors examples/anchors.jsonl --baseline examples/run_baseline.json --current examples/run_current.json

Judge-only movement with a flat live metric (synthetic):

```bash
drift-sentinel check --anchors examples/anchors.jsonl \
  --baseline examples/run_baseline.json \
  --current examples/synthetic_judge_only_current.json
# JUDGE_DRIFT, live metric +0.000 → exit 2 (see examples/synthetic_judge_only_OUTPUT.txt)
```
verdict      : JUDGE_DRIFT
anchor kappa : 0.833 -> 0.333
anchor flips : 25.0% of frozen anchors changed label
judge pin    : CHANGED frontier-4-2026-05-01@9f2c1a -> frontier-4-latest@9f2c1a
live metric  : moved -0.150
reason       : agreement with the frozen human labels fell (0.833 -> 0.333); the ruler moved, not the system
note         : judge is not pinned: frontier-4-2026-05-01@9f2c1a -> frontier-4-latest@9f2c1a
note         : live metric moved -0.150 but is untrustworthy under judge drift
```

The judge was riding a `-latest` alias, the provider updated it, and a quarter of the frozen anchors flipped label. Rolling back the deploy would have fixed nothing. Same metric drop, but with the judge holding steady on the anchors:

```
$ drift-sentinel check --anchors examples/anchors.jsonl --baseline examples/run_baseline.json --current examples/run_current_system.json
verdict      : SYSTEM_CHANGE
anchor kappa : 0.833 -> 0.833
anchor flips : 0.0% of frozen anchors changed label
judge pin    : held frontier-4-2026-05-01@9f2c1a
live metric  : moved -0.150
reason       : anchor agreement held (0.833 -> 0.833) while the live metric moved -0.150; the movement is real and belongs to your system
```

Now the rollback is justified, and you can prove it.

## Why this exists

Production eval pain is longitudinal. Cross-sectionally,
[judge-reliability-kit](https://github.com/homayoun-safarpour/judge-reliability-kit)
answers *why a judge panel disagrees right now*. The failure that burns release
time is different: scores move between weeks and nothing says whether the system
changed or the ruler did. Every incident reduced to the same missing measurement:
a frozen human-labeled reference the judge re-scores every run.

That measurement is this package. One verdict, three outcomes, CI exit codes, and
a loop-engine gate (`examples/as_loop_gate.py` + `--gate "drift=..."`) so an agent
loop repairs the scoreboard the moment it stops being trustworthy. Honest
`SYSTEM_CHANGE` stays green; only `JUDGE_DRIFT` blocks.

## Design commitments

- **No LLM dependency.** The sentinel judges the judge from score files; it never calls a model. Verdicts must be deterministic and testable.
- **Zero runtime dependencies.** Standard library only.
- **Chance-corrected, not vibes-corrected.** Agreement is Cohen's kappa (unweighted by default; linear or quadratic weights for ordinal 0-3 rubrics), so a judge that drifts toward always-pass cannot hide behind high raw accuracy.
- **The reference must be provably frozen.** `AnchorSet.freeze_hash` fingerprints the human labels; a partial re-score is rejected, not silently compared. A pinned baseline records that hash, and `drift-sentinel check` exits 1 if the anchor file no longer matches (`tests/test_baseline.py::test_check_refuses_when_pinned_baseline_freeze_hash_mismatches`).
- **Every claim above is a test.** The central one: `tests/test_verdict.py::test_drift_on_frozen_anchors_blames_the_judge_not_the_system`. Slow decay across N runs: `tests/test_history.py::test_history_flags_slow_decay_that_pairwise_checks_miss`. Judgekit bridge: `tests/test_adapter.py::test_adapter_reads_anchor_scores_straight_from_judgekit_panel_export`. Loop gate remap: `tests/test_loop_engine_gate_docs.py::test_as_loop_gate_remaps_system_change_to_pass_and_judge_drift_to_fail`.


## Related reading

- [Judge reliability and eval-score movement (arXiv:2606.15474)](https://arxiv.org/html/2606.15474): related field survey on LLM judges; this package is a separate deterministic CI gate, not that paper's code.

## Contributing

Issues and PRs welcome. Run `python -m pytest -q` and `python -m ruff check src tests` before pushing.

## Citation

```bibtex
@software{safarpour2026judgedriftsentinel,
  author = {Homayoun Safarpour},
  title  = {judge-drift-sentinel: attribute eval-score movement to the system or the judge},
  year   = {2026},
  url    = {https://github.com/homayoun-safarpour/judge-drift-sentinel}
}
```

Author: Homayoun Safarpour Â· [LinkedIn](https://www.linkedin.com/in/homayoun-safarpour/)

## License

MIT
