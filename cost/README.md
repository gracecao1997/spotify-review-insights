# Offline cost and runtime calculator

The recorded Gemma v2 pilot contains the unchanged course `cost_100.csv` IDs. It ran one worker with an empty result cache, then replayed the saved results. This is real measured execution, not a simulated estimate. No hosted model API was used. Hardware and electricity costs remain unknown.

From the project directory, run `python3 calculator.py` to recompute `cost/report.json`, `cost/report.md` and `cost/usage.csv` from saved usage and editable `cost/rates.csv`. This command makes no network or model calls and needs no API keys. `python3 calculator.py --rate-multiplier 2 --out cost/doubled.json` exercises price sensitivity; a nonzero-rate test verifies actual doubling, since zero doubled remains zero. Projection count changes do not alter recorded pilot results.

Explicit execution is separate: `python3 pilot.py --execute-local --root runs/a-new-cold-experiment`. The program refuses an existing cold-result cache. For warm replay use the same root plus `--warm`. Model requests are bounded, outputs are validated, invalid responses are retried once, and unresolved failures are visible. The implementation has no paid model endpoint, so its API spending limit is structurally $0; it does not claim a paid-provider spend ledger has been tested.

The first pilot exposed semantic errors despite passing schema validation. The prompt was then revised using development examples. The initial pilot remains evidence for its own saved configuration, not proof of the later configuration's quality or speed. Refresh measurements after checkpoints and before any full run. The `report.md` projections are scenarios, not a guarantee of completion time.

Raw evidence is under `runs/pilot-v2/`: cold and warm experiment metadata, the 100 outputs, complete per-attempt enrichment logs, independent verification, issue naming, ranking, memo, and stage-call logs. Those files must be included in the downloadable submission evidence because `runs/` is excluded from code commits. The compact copies in this folder identify the same source run.
