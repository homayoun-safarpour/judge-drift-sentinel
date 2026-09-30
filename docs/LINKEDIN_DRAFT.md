# LinkedIn draft (public-safe) - drift-sentinel first-screen restyle 2026-09-30

Field pain first. Homayoun posts himself.
Paste verified 2026-09-30 on `examples/run_current.json`: verdict JUDGE_DRIFT exit 2.

---

Paste block (copy from the next line to the URL):

Your eval score moved after a model update. That does not mean the system got worse.

drift-sentinel re-scores a frozen human anchor set. No extra LLM calls.

The stranger run is judge drift, not a clean pass:

git clone https://github.com/homayoun-safarpour/judge-drift-sentinel
cd judge-drift-sentinel && pip install -e .
drift-sentinel check --anchors examples/anchors.jsonl --baseline examples/run_baseline.json --current examples/run_current.json

verdict      : JUDGE_DRIFT
anchor kappa : 0.833 -> 0.333
reason       : the ruler moved, not the system

Exit 2 means stop trusting the scoreboard. Exit 3 means the movement is real (SYSTEM_CHANGE). Exit 0 is STABLE.

The limit: it does not replace your eval suite. It only tells you whether the judge still agrees with the frozen humans.

Repo:
https://github.com/homayoun-safarpour/judge-drift-sentinel
