# judge-drift-sentinel

**Your eval score just dropped 15 points — this tool tells you in one command whether your system regressed or your LLM judge silently changed, so you never ship (or block) a release on a broken ruler.**

[![CI](https://github.com/homayoun-safarpour/judge-drift-sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/homayoun-safarpour/judge-drift-sentinel/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## The problem

Teams that grade LLM systems with an LLM judge get a moving scoreboard and cannot tell why it moved:

| What moved | What it looks like | What teams do (wrongly) |
|---|---|---|
| The system | Eval score drops after a deploy | Roll back — correct, if it really was the system |
| The judge model | Provider ships a silent update behind `-latest` | Roll back a healthy deploy, or chase a phantom regression |
| The judge prompt | Someone "fixed" one rubric sentence in week 8 | Trust week-1 vs week-9 charts that are not comparable |
| Nothing | Ordinary judge variance | Re-run until the number looks right |

All four produce the same dashboard artifact: a number that moved. The score alone cannot tell you which one happened — you need a second measurement that isolates the judge.

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

The verdict is deterministic, computed from score files you already have, and needs zero LLM calls — so it runs in CI in milliseconds.

## Install

```bash
pip install git+https://github.com/homayoun-safarpour/judge-drift-sentinel
# or from source
git clone https://github.com/homayoun-safarpour/judge-drift-sentinel && cd judge-drift-sentinel && pip install -e .
```

## Quickstart

Label 10–50 representative outputs once, by hand — this is your anchor set (JSONL):

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

Each consecutive pair gets the same 3-way verdict as `check`. If kappa falls slowly — every step under `--kappa-drop`, but the first→last window exceeds it — history flags **slow decay** (exit 2). That is the failure mode a single pairwise gate cannot see.

Exit codes make it a drop-in quality gate: `0` = STABLE (trust your numbers), `3` = SYSTEM_CHANGE (numbers are trustworthy and your system moved), `2` = JUDGE_DRIFT or slow decay (stop — the scoreboard itself is broken).

## What is in the box

| Module | What it does | Use it when |
|---|---|---|
| `driftsentinel.anchors` | Loads the frozen anchor set, fingerprints it (`freeze_hash`) | You need proof the reference set itself never moved |
| `driftsentinel.agreement` | Cohen's kappa (unweighted) plus weighted linear/quadratic kappa for ordinal 0-3 rubrics; observed agreement; flip rate — stdlib only | You want chance-corrected agreement, including near-vs-far misses on ordinal scales |
| `driftsentinel.runs` | One judge run: model + prompt fingerprint + anchor scores | "Pin your judge" as data, not as a slogan |
| `driftsentinel.verdict` | The 3-way attribution policy, fully unit-tested | You need "who moved?", not another score |
| `driftsentinel.baseline` | Score a run and freeze it as a pinned baseline (with `anchor_freeze_hash`); `check` refuses on hash mismatch | You want a durable reference that cannot silently drift |
| `driftsentinel.history` | Verdict + kappa timeline across N runs; flags slow decay pairwise checks miss | Weekly/monthly pinned runs where erosion is gradual |
| `driftsentinel.cli` | `drift-sentinel baseline` / `check` / `history`, plain or `--json`, gate-friendly exit codes | Wiring the verdict into CI, cron, or an agent loop |

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

The `examples/` folder ships both failure stories. In July the judge was pinned and agreed with the human labels at kappa 0.83. In August the live eval metric dropped from 0.81 to 0.66 — a 15-point fall that looks exactly like a system regression. Ask the sentinel:

```
$ drift-sentinel check --anchors examples/anchors.jsonl --baseline examples/run_baseline.json --current examples/run_current.json
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

Now the rollback is justified — and you can prove it.

## Why this exists

I run agent-driven daily project loops and build instruments for judging and evaluating them. My [judge-reliability-kit](https://github.com/homayoun-safarpour/judge-reliability-kit) answers the cross-sectional question: *why does a judge panel disagree right now?* But the failure that actually burned time was longitudinal: scores moved between weeks and nothing could say whether the systems changed or the ruler did. Every incident reduced to the same missing measurement — a frozen human-labeled reference the judge re-scores every run. So the measurement became a package: one verdict, three outcomes, and exit codes that [agent-loop-engine](https://github.com/homayoun-safarpour/agent-loop-engine) can consume as a quality gate (`--gate "judge=drift-sentinel check ..."`), so an agent loop halts itself the moment its own scoreboard stops being trustworthy.

## Design commitments

- **No LLM dependency.** The sentinel judges the judge from score files; it never calls a model. Verdicts must be deterministic and testable.
- **Zero runtime dependencies.** Standard library only.
- **Chance-corrected, not vibes-corrected.** Agreement is Cohen's kappa (unweighted by default; linear or quadratic weights for ordinal 0-3 rubrics), so a judge that drifts toward always-pass cannot hide behind high raw accuracy.
- **The reference must be provably frozen.** `AnchorSet.freeze_hash` fingerprints the human labels; a partial re-score is rejected, not silently compared. A pinned baseline records that hash, and `drift-sentinel check` exits 1 if the anchor file no longer matches (`tests/test_baseline.py::test_check_refuses_when_pinned_baseline_freeze_hash_mismatches`).
- **Every claim above is a test.** The central one: `tests/test_verdict.py::test_drift_on_frozen_anchors_blames_the_judge_not_the_system`. Slow decay across N runs: `tests/test_history.py::test_history_flags_slow_decay_that_pairwise_checks_miss`.

## Contributing

Issues and PRs welcome. Run `python -m pytest -q` and `python -m ruff check src tests` before pushing.

## Citation

```bibtex
@software{safarpour2026judgedriftsentinel,
  author = {Safarpour Dehkordi, Homayoun},
  title  = {judge-drift-sentinel: attribute eval-score movement to the system or the judge},
  year   = {2026},
  url    = {https://github.com/homayoun-safarpour/judge-drift-sentinel}
}
```

## License

MIT
