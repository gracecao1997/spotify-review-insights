# Development evidence and outstanding decisions

## Completed foundations

The supplied archive was read without modifying its source. The full CSV's checksum matches the manifest. The supplied checker profiled 660,622 original IDs, 13 empty reviews, 159,701 missing app versions, and zero duplicate IDs. Exact-text inspection found 484,189 distinct nonempty texts.

A local labeling form presents the 50 golden reviews without star ratings or model answers. Save/reload/export was tested against a synthetic case in a temporary database; no test labels were written into the student's golden set. The student must independently fill all 50 labels before final evaluation.

The pipeline uses Python's standard library, SQLite, bounded local Ollama calls, schema validation, exact-source hashing, cache provenance and atomic batch commits. The ranking arithmetic and CSV handling have focused tests. A local dashboard reads saved processed reviews, ranking data and a memo from SQLite through a Python HTTP backend. Its provisional development status is explicit. It has not been publicly deployed.

## Actual experiments

1. Gemma v1, ten reviews: all ten failed validation because the model changed quotes or supplied entities absent from the text. This failure is retained under `runs/benchmark/`.
2. Gemma v2: code extraction followed the assignment's recommendation, preserving the full original review as its exact evidence span and matching entity strings against a declared glossary. The ten-review structural benchmark completed, followed by a real full 100-review cold/warm pipeline.
3. The v2 full pilot took 180.656 seconds cold and 0.033 seconds warm. The warm run made zero new enrichment calls. All 100 labels were structurally valid, but inspection found wrong topic/severity/intent decisions; this is not an accuracy claim. Raw measurements, prompts, outputs and rates are retained.
4. The v2 independent verifier detected a deliberately wrong synthetic label and handled a synthetic embedded instruction as review data. These synthetic records are separate from business results.
5. Qwen3 4B was downloaded from the official Ollama registry as a free local alternative named among the assignment's candidate families. Its 30-review test and an incomplete later pilot are retained. It was slower here and still made taxonomy errors. The incomplete experiment was stopped and must not be represented as a completed pilot. Short test timings included model-loading and queue variability and are not a reliable production throughput estimate.
6. Gemma v3 added boundary examples using development/synthetic cases only. The two generic-criticism examples changed to the rubric-supported severity 2, but other topic errors remained. Twenty outputs were saved. A 500-review run then started with an actual SIGINT after a committed batch, followed by resume. Its recording and before/after snapshots are saved under `runs/checkpoint-recovery-v3/` as execution proceeds.

No hosted API calls, model-credit purchases or paid deployments were made. Local hardware and electricity cost are unknown, not zero. The original v2 cost report applies to that configuration; the v3 checkpoint is a later configuration and needs separately reported measurements.

## Decisions still requiring the student's input

- Complete the 50 human labels. They must not be fabricated or replaced with assistant/model labels.
- Confirm today's class time and whether the instructor accepts 100,000 classifications for full coverage credit. The Word document and supplied grading contract conflict on this point.
- Confirm whether an existing Jev/TypeSafe account has available credit. The official API is paid; no free credit has been verified for this account. Do not send keys in chat.
- After a viable scale route is measured, finish the 10,000-review checkpoint, full run, final human evaluation, final memo, public backend/database/dashboard deployment, repository and submission evidence.

## Reference-based decisions

The assignment's `COST_CALCULATOR.md` explicitly recommends deterministic extraction and fixed-label classification, and permits local models. These instructions motivated moving quotes/entities out of model generation and testing a Qwen alternative. The official TypeSafe quick start and models documentation were checked as a possible faster classification route; their pricing and rate limits are not assumed to be free or guaranteed for this account. No provider marketing benchmark is treated as our measured throughput.

## Jev migration and completed human set — 2026-10-06

- Student reports instructor approval for 100,000 reviews, Jev recommendation, and a maximum $10 budget.
- Deterministic scope prepared: 100,000 nonempty + 13 empty, 78,099 distinct nonempty texts. Original full profile remains separate.
- Human set verified and backed up: 50 labels, 7 needs-review. No golden answers were read into or used to tune model prompts.
- Added shared durable budget ledger, explicit paid classifier, independent blind verifier, cached mixed-provider six-stage orchestration, and offline Jev calculator.
- Added synthetic transport tests for integer severity, provider mismatch, timeout reservations, concurrent budget admission, one retry, exact duplicate reuse, warm zero-call behavior, and editable cost arithmetic. These tests do not constitute real Jev inference or billing evidence.
- Jev execution awaits a locally configured API key. Final classification, golden evaluation, Jev cold/warm measurements, final memo and public deployment remain outstanding.

## Transport interruption and explicit recovery

The first Jev 10,000-review expansion stopped after 8,912 completed records, one network-failed quarantine and 1,087 pending records. Three consecutive transport failures triggered the circuit breaker; saved results were retained. HTTPS connectivity was subsequently confirmed without a paid request. The interrupted output folder was preserved before resume.

Added an explicit `--retry-transport-quarantine` recovery option that reopens only quarantines caused by network errors or HTTP 5xx responses, preserving their prior payloads and every attempted call. Invalid model-output quarantines and empty rows are not reopened by this option. Unknown charges remain reserved in the shared budget ledger. Synthetic recovery tests verify preservation of attempts/reservations and completion on a later successful request. The resumed checkpoint reuses all completed classifications.
