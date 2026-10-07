# Offline Jev pilot replay

From the repository root, run `python3 jev_calculator.py`. This reads only the committed files in this directory and `cost/jev_rates.csv`; no API key, model server, source dataset or `runs/` directory is needed.

`cold_calls.jsonl` identifies the measured cold calls. `pilot_calls.jsonl` contains the cumulative cold/warm attempted calls. Their set difference is warm incremental usage. `pilot_records.jsonl` preserves the fixed 100 source IDs, source row hashes, outcomes and exact-text provenance. The two experiment JSON files preserve measured wall times and configuration.

Prices are editable in `../jev_rates.csv`, with dollars per million tokens and dated source links. The report keeps API spend separate from unmeasured local hardware/energy cost. Outputs are free for the pinned Jev model at the recorded rate; local Ollama API fees are zero.

To perform a new paid pilot, use `python3 jev_pipeline.py --execute-paid --pilot --root runs/new-pilot`, followed by the same command with `--warm`. This is separate from offline replay and uses the project-wide spend ledger. Never erase prior evidence to claim an empty cold cache.

The recorded pilot is real. Unit tests use synthetic transports only to exercise retries and budget failure paths, and are not model-execution evidence. The original local-model pilot in the parent folder is retained as historical experimentation, not substituted for this Jev pilot.
