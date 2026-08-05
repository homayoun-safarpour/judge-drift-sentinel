# Interview notes — judge-drift-sentinel

## Three questions

1. Why can a live eval metric move without the system under test changing?
2. What does a frozen human-labeled anchor set isolate that a live metric cannot?
3. How do exit codes from `drift-sentinel check` plug into CI or an agent loop gate?

## Two-minute demo

```bash
pip install judge-drift-sentinel
# or: git clone … && pip install -e ".[dev]"
drift-sentinel baseline examples/run_baseline.json --anchors examples/anchors.jsonl -o /tmp/baseline.json
drift-sentinel check examples/run_system_change.json --baseline /tmp/baseline.json --anchors examples/anchors.jsonl
echo Exit:$LASTEXITCODE
```

Show the verdict (`SYSTEM_CHANGE` / `JUDGE_DRIFT` / `STABLE`) and that the command needs no LLM calls.

## Limitations

- Anchor quality bounds the method: biased or tiny anchors produce noisy kappa.
- Does not replace system evals; it attributes movement of a score you already compute.
- Weighted kappa helps ordinal rubrics; it does not invent labels the humans never provided.
