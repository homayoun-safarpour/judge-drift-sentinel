# Interview talking points: judge-drift-sentinel

Five CLI-backed points for a technical screen (no resume recap).

- **`drift-sentinel baseline RUN.json --anchors anchors.jsonl -o baseline.json`** :  pins human-labeled anchors (`anchor_freeze_hash`) so later runs compare against the same ruler, not a moving rubric.
- **`drift-sentinel check CURRENT.json --baseline baseline.json --anchors anchors.jsonl`** :  attributes score movement: `STABLE`, `SYSTEM_CHANGE`, or `JUDGE_DRIFT`; exit codes are shaped for CI (trust the number only when the judge agreement held).
- **Frozen anchors isolate the judge** :  humans never change in the anchor set, so a drop in kappa vs humans means the judge or prompt moved, not necessarily your deploy.
- **`drift-sentinel history --anchors anchors.jsonl --runs run1.json run2.json`** :  timeline of verdicts catches slow judge decay that pairwise `check` might miss in isolation. Worked multi-run fixture: `examples/drifting/` (expect exit 2).
- **`drift-sentinel import-judgekit --panel panel_export.json`** :  bridges a judge-reliability-kit panel export into sentinel anchor/run JSON so you do not re-label examples twice.

## Related instruments

- [judge-field-guide](https://github.com/homayoun-safarpour/judge-field-guide) - CI-tested map of the LLM-judge ecosystem
- [judge-reliability-kit](https://github.com/homayoun-safarpour/judge-reliability-kit) - why a judge panel disagrees (kappa)

