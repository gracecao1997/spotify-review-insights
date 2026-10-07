# Final submission review against the assignment and October 6 clarification

This is an evidence review, not an instructor grade. The original course checker is unchanged. No new paid model calls or label changes were made during this review.

## Classroom clarification

The student-supplied October 6 transcript explicitly changes the requirement to at least 100,000 reviews and recommends a total API cost within $10. It also requires an inspectable dashboard, backend and database, and emphasizes standalone execution, distinct model roles, bounded tasks and saved checkpoints. Later discussion allows the same model to serve distinct roles; a costly swarm or multiple providers is not required. The recording is a noisy automatic transcript, so its garbled model names and price units are not authoritative pricing references. The full private transcript is not published here.

The submission classifies 100,000 nonempty source reviews and quarantines all 13 empty records. This satisfies the clarified scope. The assignment retains some older full-corpus paragraphs and a full-corpus denominator formula; that inconsistency is disclosed rather than silently changing the supplied checker or claiming all 660,609 texts were classified.

## Findings and corrections

| Finding | Action and remaining limit |
|---|---|
| Stale setup and unfinished-work language | README now identifies the completed scope, actual final Qwen writer, dependency versions, downloadable artifacts and clean replay commands. |
| Dashboard recommendation lacked adjacent numeric citations | Dashboard now attaches the saved priority count, score, mean, claim IDs and model-selected review IDs, with a direct evidence action. No labels or recommendation text were regenerated. |
| Error analysis listed discrepancies without interpreting examples | Added explicit rubric-based examination of severity, premium/control boundaries, resolved versus old complaints, foreign-language uncertainty, entity extraction limits and verifier differences. Original human labels and predictions remain unchanged. |
| Source trace did not include blind verification | Added a second complete trace from a verifier-sampled source review to membership, ranking and issue-level memo claims. |
| Calculator lacked visible planning controls and original full-volume scenario | Added editable budget/reserve, verification/fallback assumptions, output/worker limits, original full-corpus projection, per-stage tables and cost/throughput metrics. Planning limits are not presented as measured speedups. |
| Replay relied on the developer's local run folders | Release now includes final settings, experiment, reference and memo. `verify_saved.py` recomputes ranking directly from saved membership; clean-directory replay checks the calculator, ranking, original audit and database reconstruction without credentials. |
| Rubric evidence map too broad | README now links each of the ten criteria and includes stage input/output, stop and retry contracts. |

## Remaining potential deductions — not concealed

1. **Unknown usage for failed requests (moderate risk).** Eleven transport/server failures returned no token usage. The unchanged checker emits 22 `invalid_usage` field flags and remains `review_required`. Known spend is calculated from real usage; conservative reservations remain. Missing values are not replaced with fabricated zeroes. The instructor may accept the disclosure or require provider billing reconciliation.
2. **No retained contemporaneous standalone 500-review projection (moderate risk under T3).** Real 500-review calls, outputs, timings and recovery are saved, and a 10k projection gate is retained. The supplemental 500 projection is explicitly retrospective. It cannot prove a standalone forecast existed before scaling.
3. **No single total end-to-end project timer (low-to-moderate risk).** The real cold/warm pilot and individual run segments have measured wall times. Final resumed pipeline time is 5,280.950 seconds, including 5,086.483 seconds of classification. It is not the total of the interrupted development process. Summed overlapping call times are not substituted for elapsed time.
4. **Interpretation quality (moderate risk).** Topic/intent/severity agreement is 78%/82%/72%, and needs-review agreement is 52%. The rubric specifies no minimum accuracy, but coarse categories, shared-model verification and uncalibrated uncertainty can weaken the business recommendation. Agreement can hide shared human/model errors. The recommendation is a diagnostic priority, not an engineering ROI estimate.
5. **Final explanation and submission remain the student's responsibility.** Read the decision memo and be prepared to explain one source trace, one failure, the cost calculation and resume behavior. The repository has not been submitted in bCourses by this program. No claim of a guaranteed score is made.

High confidence: scope clarification, completed counts, deterministic calculations and actual saved test results. Moderate confidence: semantic diagnoses and likely grading implications. The instructor determines the final score.

See [README](README.md), [decision memo](DECISION_MEMO.md), [clean replay evidence](evidence/submission_replay.json), [regression output](evidence/regression_tests.txt) and [original audit disclosure](evidence/audit-disclosure.json).
