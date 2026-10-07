# Spotify product priority: investigate usability first

This is an AI-assisted analytical review of the saved pipeline outputs. The separately logged model-generated memo remains available in `evidence/final-memo.md`; this document adds interpretation and explicit alternatives without changing any classification.

## Decision and supporting evidence

Prioritize investigation of **usability complaints**, then use focused review of the underlying reports to select a concrete interface, advertising, or playlist-management problem for engineering. The baseline ranks usability first: **12,350 complaint/cancellation reviews**, severity sum **30,007**, and mean severity **2.429717** [C001–C003 in `evidence/final-claims.csv`]. This is the strongest issue under the required frequency-times-severity rule, not evidence that one specific feature explains all usability complaints.

The recommended next step is a scoped diagnostic exercise: separate navigation/control problems, playlist-management failures and advertising interruptions within the usability group; inspect original reports; and test candidate fixes against the reported behavior. No implementation cost, causal impact or retention gain can be estimated from this dataset.

## Alternatives and tradeoffs

- **Other** ranks second, with 14,325 complaints and a severity sum of 28,089 [C004–C006]. Its higher complaint count does not identify an actionable defect: this category includes generic criticism and insufficiently specific reports. Review it for classification limitations, rather than treating it as a single engineering project.
- **Billing and playback** have nearly equal severity sums: 20,975 and 20,902 [C008, C011]. Playback has fewer complaints but higher mean severity: 3.177079 versus billing's 2.701223 [C009, C012]. The baseline alone does not justify a strong preference between these two alternatives.
- **Access** has the highest mean severity among the issue groups, 3.910067, but only 1,490 complaints and a severity sum of 5,826 [C013–C015]. A team focused on blocked core tasks might investigate access before lower-impact usability annoyances. That is a different objective from the required baseline and should be stated explicitly.

## Traceable examples

These illustrate reported experiences, not their prevalence or confirmed technical causes:

- `117770a7-cec9-4bc3-8a9f-a5d6f3544b5d` mentions ads and difficulty using the app.
- `1b72a43a-0608-4b73-991a-b9fbe84a5ebc` reports losing liked songs.
- `1e4d3214-63de-4ba0-9870-a4ee8aa32942` describes loud, frequent ads and makes an unverified allegation about data use. The allegation must not be presented as a confirmed privacy violation.

Each ID is preserved in `grading/records.jsonl`; `grading/membership.csv` assigns it to an issue; `grading/ranking.csv` recomputes the issue metrics; and `grading/claims.csv` links the numeric claims above. The release archive contains these artifacts and the analysis input.

## Scope and limitations

The analysis covers a deterministic professor-approved sample of 100,000 nonempty reviews plus 13 empty records, drawn from the supplied historical May 2022–November 2023 snapshot. All 660,622 source rows were profiled, but the entire corpus was not classified. Every source ID in the selected sample is accounted for, and exact-text caching preserves duplicate rows in aggregates.

Held-out human/model agreement is 78% for topic, 82% for intent and 72% for severity; severity mean absolute error is 0.38. Seven human-marked uncertain cases remain in the main denominator. These figures measure agreement, not definitive truth. Independent blind verification of 1,000 final-run records found 16 topic, 11 intent and 25 severity disagreements. Shared-model verification can preserve shared errors.

Broad primary-topic grouping, self-selection, historical timing and classification errors limit the recommendation. Reviews do not measure the whole customer population, observed churn, revenue at risk or the causal value of a proposed fix. Eleven failed API requests have unavailable token usage; the original course audit flags them and their conservative budget reservations are retained.
