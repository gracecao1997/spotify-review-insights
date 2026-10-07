# Offline Jev pilot replay

From the repository root, run `python3 jev_calculator.py`. This reads only the committed files in this directory and `cost/jev_rates.csv`; no API key, model server, source dataset or `runs/` directory is needed.

`cold_calls.jsonl` identifies the measured cold calls. `pilot_calls.jsonl` contains the cumulative cold/warm attempted calls. Their set difference is warm incremental usage. `pilot_records.jsonl` preserves the fixed 100 source IDs, source row hashes, outcomes and exact-text provenance. The two experiment JSON files preserve measured wall times and configuration.

Prices are editable in `../jev_rates.csv`, with dollars per million tokens and dated source links. The report keeps API spend separate from unmeasured local hardware/energy cost. Outputs are free for the pinned Jev model at the recorded rate; local Ollama API fees are zero.

To perform a new paid pilot, use `python3 jev_pipeline.py --execute-paid --pilot --root runs/new-pilot`, followed by the same command with `--warm`. This is separate from offline replay and uses the project-wide spend ledger. Never erase prior evidence to claim an empty cold cache.

The recorded pilot is real. Unit tests use synthetic transports only to exercise retries and budget failure paths, and are not model-execution evidence. The original local-model pilot in the parent folder is retained as historical experimentation, not substituted for this Jev pilot.


Editable planning controls (do not launch calls or change historical measurements):

```sh
python3 jev_calculator.py --budget 10 --reserve-margin 1 --max-workers 2 --output-token-cap 2200 --verify-fraction .01 --fallback-fraction 0
python3 jev_calculator.py --nonempty 660609 --distinct 484189 --out runs/full-corpus-projection
```

The second command provides the original 660,622-row assignment scenario: 660,609 nonempty inputs plus 13 quarantines, with a no-cache comparison and a conservative 20% extra-attempt case. It is an estimate, not execution. The approved submission uses 100,000 nonempty inputs instead. The full scenario exceeds the current budget and must not be silently executed.

No paid fallback was used. A hypothetical nonzero fallback fraction requires explicit `--fallback-usd-per-record` and `--fallback-seconds-per-record`; the calculator refuses missing assumptions. Worker and local output-cap changes are recorded as planning limits, not fabricated speedups or measured token savings. Jev returns a fixed response schema rather than generative text controlled by an output-token parameter. Actual local generation used cap 2,200, and actual workers were one for the pilot and two for the final run.

`tests/test_jev_calculator.py` checks rate doubling, unchanged recorded time/local cost, volume invariance, budget warnings and zero warm enrichment. Stage role requests, original prompt/schema hashes and raw usage are preserved in `pilot_calls.jsonl`; `cold_experiment.json` preserves local model settings. `report.json` contains stage arithmetic, units, throughput and cost per input/completed review.
