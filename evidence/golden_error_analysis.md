# Held-out human/model comparison

All 50 human labels were completed before evaluation. Prompts are frozen at jev-review-v1; no golden errors were used to tune them. These are agreement measurements, not proof that either side is always correct.

| Field | Agreement |
|---|---:|
| topic | 78% |
| intent | 82% |
| severity | 72% |
| needs_review | 52% |
| sentiment_within_0.5 | 100% |
| evidence_exact_substring | 100% |
| entities_exact_set | 50% |

Severity mean absolute error: 0.38.

Seven human needs-review cases remain in the main denominator. The separate diagnostic subset does not claim they have definitive labels.

## Disagreements to inspect

| Review ID | Field | Human | Model |
|---|---|---|---|
| 292ce26a-815d-4bce-a3b6-93cb6c9e7e2c | severity | 5 | 2 |
| 991b6b3a-f511-458a-a5b7-234f78048fb5 | severity | 2 | 3 |
| 991b6b3a-f511-458a-a5b7-234f78048fb5 | needs_review | False | True |
| 599a0d41-989a-40ef-8ed2-e92db76eea46 | needs_review | False | True |
| 111f9048-f7bd-4be0-813e-76b8fc49f73f | needs_review | False | True |
| b567f70c-edba-4922-ac2a-e945e5eb3472 | needs_review | False | True |
| b5ee7834-a0eb-4c15-9c7b-935831021922 | needs_review | False | True |
| 1fc8b08f-7d6a-472f-b317-8ceb28d00f22 | topic | billing | usability |
| 1fc8b08f-7d6a-472f-b317-8ceb28d00f22 | needs_review | False | True |
| 723f07de-9881-4049-8680-1a9e25652914 | topic | support | playback |
| 723f07de-9881-4049-8680-1a9e25652914 | intent | unclear | complaint |
| 723f07de-9881-4049-8680-1a9e25652914 | severity | 1 | 4 |
| 47428620-ec21-424d-a515-0b0b0012a5cf | needs_review | False | True |
| fc344263-308d-48a1-9715-c380d063b6de | needs_review | False | True |
| 6112667b-3d71-475c-b1a4-159b87f73d2b | needs_review | False | True |
| 01d453b0-dca3-42e9-8aa4-5fc167b08070 | needs_review | False | True |
| ac6cd66d-a9d2-42a4-afb8-2f84beff7fd1 | topic | other | catalog |
| ac6cd66d-a9d2-42a4-afb8-2f84beff7fd1 | intent | unclear | request |
| ac6cd66d-a9d2-42a4-afb8-2f84beff7fd1 | severity | 2 | 1 |
| 46842184-32f8-4088-ac15-2a700a7e94ed | topic | other | catalog |
| 46842184-32f8-4088-ac15-2a700a7e94ed | intent | unclear | complaint |
| 46842184-32f8-4088-ac15-2a700a7e94ed | severity | 1 | 2 |
| 5de7f95b-ccad-41b2-9f63-a13f7c1d9f09 | intent | complaint | unclear |
| 5de7f95b-ccad-41b2-9f63-a13f7c1d9f09 | needs_review | False | True |
| 372d4e67-59cc-4c54-879f-3e8a202ee554 | needs_review | True | False |
| 47f1406d-4918-4d60-9647-5ca8e610caca | severity | 2 | 4 |
| 82780cbe-6435-4efb-84f6-8e5fa47ffc3a | needs_review | False | True |
| f4c8146a-d5c8-4168-b00e-21af666afc6a | intent | unclear | praise |
| 3ddb3f4e-f7b9-430b-b335-eadc6d321f46 | severity | 4 | 3 |
| 16d640e9-b281-4746-9562-c7dbcf7126b6 | severity | 2 | 3 |
| 8cc4fad4-26ec-47b7-96e8-49c7da714eca | intent | unclear | complaint |
| 8cc4fad4-26ec-47b7-96e8-49c7da714eca | severity | 1 | 2 |
| 8cc4fad4-26ec-47b7-96e8-49c7da714eca | needs_review | False | True |
| 215463ae-95b7-4481-8747-1754b68f31fa | topic | usability | playback |
| 215463ae-95b7-4481-8747-1754b68f31fa | intent | request | complaint |
| 46c0b49f-83a1-427e-8f0b-cef62e3c94b5 | severity | 3 | 2 |
| 283b5843-a992-464f-b1dc-9dc7281ff390 | topic | other | billing |
| 1d15724a-98ff-400a-8083-0d9afc801098 | needs_review | False | True |
| 89ea724c-358f-48ab-9516-cd130d21c471 | needs_review | False | True |
| 2aa566c6-b98d-4513-b900-83702a8db8eb | topic | other | usability |
| 8c0546b0-ce43-4a36-9d33-9f979e98d522 | topic | playback | catalog |
| 8c0546b0-ce43-4a36-9d33-9f979e98d522 | intent | request | complaint |
| a972945c-6601-4108-882a-afe986866a7b | needs_review | False | True |
| 8fd3dd72-5535-40f6-8779-1bd60892131e | needs_review | False | True |
| b58dd6f0-ad88-4319-b6db-58afb60c37c1 | needs_review | False | True |
| 1a41c7e1-a655-4c63-b4db-c22bdff18003 | severity | 1 | 2 |
| 1a41c7e1-a655-4c63-b4db-c22bdff18003 | needs_review | False | True |
| dceb14e7-2df0-422f-bb2b-73d7c373159a | topic | usability | playback |
| dceb14e7-2df0-422f-bb2b-73d7c373159a | needs_review | False | True |
| ac4e860a-c042-49cc-90f3-189591c336ac | topic | playback | downloads |
| ac4e860a-c042-49cc-90f3-189591c336ac | intent | request | complaint |
| ac4e860a-c042-49cc-90f3-189591c336ac | severity | 4 | 3 |
| ac4e860a-c042-49cc-90f3-189591c336ac | needs_review | False | True |
| d2f3874f-d15d-4a2f-bb97-4f1213defa46 | topic | usability | billing |
| d2f3874f-d15d-4a2f-bb97-4f1213defa46 | severity | 2 | 3 |
| d2f3874f-d15d-4a2f-bb97-4f1213defa46 | needs_review | False | True |
| 99b93e31-9f15-4daa-88ac-349ab0419c48 | severity | 1 | 2 |
| 083811c7-d469-499b-9bef-5b9fb096653d | needs_review | False | True |

## Interpretation

- Needs-review agreement is low: the model also flags low-confidence outputs, while human flags may reflect language unfamiliarity. These are related but different signals.
- Exact entity-set agreement is sensitive to the fixed extraction glossary and to how many terms the human selected. Exact copying does not establish relevance or complete recall.
- Sentiment uses a continuous model score and five human categories. The predeclared ±0.5 agreement is reported alongside mean absolute error.
- Do not edit human labels to match the model. Review disagreements as limitations; any post-evaluation prompt tuning would require fresh held-out evaluation.

## Post-run semantic inspection (AI-assisted, not new human labels)

These are diagnostic interpretations of the original saved cases. Neither expected labels, predictions, prompts nor scores were changed; this review did not tune the classifier. Confidence describes the interpretation, not a new gold-standard adjudication.

| Review ID | Diagnosis against the shared rubric | Handling / confidence |
|---|---|---|
| 292ce26a-815d-4bce-a3b6-93cb6c9e7e2c | Human severity 5 versus model 2. The text criticizes content removal but does not report explicit serious financial, privacy or data harm. Strong language alone does not justify 5. | Likely human severity overstatement; keep both original labels. High confidence that 5 lacks rubric support. |
| 47f1406d-4918-4d60-9647-5ca8e610caca | Human severity 2 versus model 4. “cannot playback the songs” supports a blocked core task, beyond generic annoyance. | Model interpretation better supported; no score adjustment. Moderate confidence because the extent of failure is not fully described. |
| 3ddb3f4e-f7b9-430b-b335-eadc6d321f46 | Both human and model chose usability, yet the review explicitly links restricted controls to upgrading to Premium. The contract puts explicitly premium-only controls under billing. | A shared error can be hidden by agreement. Candidate billing boundary failure; preserve outputs. Moderate confidence. |
| 723f07de-9881-4049-8680-1a9e25652914 | The human quote selects a new update saying support resolved the problem; the model's full-text quote includes an older report of repeated crashes. This explains support/unclear/1 versus playback/complaint/4. | Temporal contradiction; the model's needs_review=false deserves scrutiny. Do not infer the historical crash is still active. High confidence that the text contains conflicting time states. |
| dceb14e7-2df0-422f-bb2b-73d7c373159a | Human usability versus model playback. Inability to choose or rewind songs can describe controls, rather than a playback engine failure. | Likely model boundary ambiguity; model already flagged needs_review. Moderate confidence. |
| ac4e860a-c042-49cc-90f3-189591c336ac | Offline-mode failure belongs under downloads. A paid subscription mention alone does not make it billing; a reported failure takes intent precedence over a request. Severity 3 versus 4 depends on whether the task is fully blocked. | Model topic/intent better follow the contract; severity remains ambiguous. High confidence on topic, moderate on severity. |
| ac6cd66d-a9d2-42a4-afb8-2f84beff7fd1 | Human marked unfamiliar/uncertain language and supplied placeholder labels; the model also flagged needs_review. | Retain in the denominator; do not treat a placeholder as independently verified meaning. A qualified language reader would be needed for definitive adjudication. |
| 283b5843-a992-464f-b1dc-9dc7281ff390 | Incoherent money-related wording led the model to billing despite unclear intent. A monetary token alone may not establish a billing issue. | Likely model over-specific topic; needs_review=true retained. Moderate confidence. |

Quotes are all exact source substrings, but the resolved-versus-old complaint case shows why substring validation is insufficient. The glossary returns only literal substrings (for example, “Premium” and “shuffle”), so it avoids invented entity spelling but can miss synonyms, other languages and relevance. In the “Nice app, very less advertising” case it returns no entities: the glossary is incomplete even though its empty set matches the human annotation. Exact entity-set agreement of 50% is therefore not entity precision or recall.

## Independent verifier disagreement inspection

Review `ab139d82-7d75-412c-bc41-8d3b2fc820b3` praises compatibility and ease of use. Enrichment selected other; the blind verifier selected usability. A specific praised feature should take precedence over generic praise, so usability is better supported (moderate confidence). No production label was replaced. Review `c4040b0d-2804-42e2-9125-e2b5eda03cce` mixes praise for listening with repeated ads; both tasks choose usability/complaint/severity 2. Its complete source → verifier → membership → memo-calculation chain is saved in `verified_source_trace.json`. This agreement does not remove the shared-model bias limitation.
