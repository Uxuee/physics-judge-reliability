# Study protocol — draft, not preregistered

## Status and hypotheses

This is an offline development protocol. No model integration, budget guard, live
experiment or confirmatory dataset exists yet. Decisions below must be reviewed
before freezing the design. Passing software tests does not validate annotations.

H1: nonzero valid-pair flip probability under equivalent wording (replication aim).
H2: detection recall for invalid reasoning with a correct final answer is lower
than for matched invalid reasoning with an incorrect final answer.
H3: physics-specific instructions improve incorrect-solution detection recall over
generic instructions. False-positive rate and overall strict accuracy are safeguards.
H4: a nonzero stable-wrong proportion shows why stability cannot establish correctness.
H1/H4 are occurrence/rate targets; one observed event is descriptive evidence, not
an automatically significant confirmatory finding. Minimum meaningful effects,
model conditions, sample size, alpha and multiplicity family remain to be frozen.

## Labels and analysis units

CORRECT means both essential reasoning and final answer are correct under the stated
assumptions. INCORRECT is the positive class for error detection. Item IDs identify
solutions; problem_id identifies the underlying question shared by solution variants.

A row is one scheduled prompt pair for one item, rubric and repetition. Include rows
for failures and missing responses; never create the analysis table from successful
calls only. Retries are attempts at the same scheduled call, not extra observations.
The helper functions compute descriptive row-level ratios. Do not interpret rows as
independent samples or pool conditions. Freeze equal repeat counts per item. Inferential
comparisons average repetitions and arms within item, then matched variants within
problem as specified below. Bootstrap entire problem_id clusters, retaining all
variants, rubrics, arms and repeats together. Report unique problem and item counts.
If upstream summaries share a source document, consider that higher-level dependency.

## Exact scoring estimands and denominators

For N scheduled pairs in one model/rubric cell, let V have two valid labels, A agree
and D disagree; A+D=V. Gold is not required for these stability quantities.

| Quantity | Definition |
| --- | --- |
| Valid-pair JSS | A/V |
| Verdict flip rate | D/V; complements JSS only on valid pairs |
| Pair coverage | V/N |
| Strict agreement | A/N; invalid pairs receive zero credit |
| Invalid-output rate | Invalid or missing arms divided by 2N |
| Strict arm accuracy | Correct selected-arm labels divided by N gold-labeled rows |
| Valid arm accuracy | Correct selected-arm labels divided by valid selected-arm labels |
| Arm coverage | Valid selected-arm labels divided by N |

The invalid-output rate includes absent responses; future generation logs must
separately distinguish transport failure, missing response and malformed returned text.
Strict agreement failure includes parsing failures and is NOT called verdict flipping.
Both malformed and incomplete outputs have parser status invalid. Exact canonical
labels after whitespace stripping are accepted; no substring matching, explanation
extraction or case guessing. Coherence supports tokens 1 through 5, including integer
inputs; booleans and floats are invalid. Parser version: strict-label-v1.

For binary physics correctness, missing or invalid gold is a dataset error: stop
correctness scoring rather than counting it as a model error. Stability still works.
Arm A accuracy does not depend on B being valid, or vice versa.

INCORRECT detection: TP=positive predictions on gold INCORRECT; FP=positive predictions
on gold CORRECT; FN=gold INCORRECT without a valid positive prediction (including
invalid outputs). TN requires a valid CORRECT prediction on gold CORRECT. Invalid
gold-negative cases are counted separately, not credited as TN. Precision=TP/(TP+FP),
recall=TP/(TP+FN), F1=2TP/(2TP+FP+FN). Always report coverage and invalid counts.

Joint categories use all N gold-labeled pairs: stable_correct (both equal gold),
stable_wrong (both valid, equal, and wrong), unstable (both valid but different),
invalid_incomplete (either arm invalid/missing). Divide each count by N; the four
proportions sum to one for N>0. These descriptive proportions differ from valid-only
JSS denominators. Never label two invalid outputs stable-wrong or stable-correct.

All undefined ratios return None / JSON null, never NaN or an invented perfect score.
Empty metric inputs yield zero counts and null rates; dataset loading rejects an
empty dataset. With gold positives but no positive predictions, precision is null,
recall and F1 are zero. With no gold or predicted positives, precision/recall/F1 are
null. Missing gold on nonempty correctness inputs raises ValueError.

## Paired endpoints and uncertainty

H3 primary endpoint: for each gold-incorrect item, average successful detection
indicators over the two arms and fixed repetitions within each rubric; invalid outputs
score zero. Subtract generic from physics-specific. Average matched variant differences
within each problem, then average equally over problems containing eligible items.
This estimates the paired change in detection recall under the frozen design. Report
problem-cluster bootstrap intervals for the paired difference, not independent-arm
interval comparisons. On gold-correct variants, report the corresponding probability
of a false INCORRECT prediction and invalid rate separately, plus strict accuracy.

H2 endpoint: within each problem and rubric, subtract detection rate on invalid
reasoning/correct-answer variants from that on invalid reasoning/incorrect-answer
variants, averaging fixed arms/repeats first. Positive differences support H2.
Predefine error matching; do not attribute effects to final answers if error severity,
wording or length differs systematically. Current fixtures cannot estimate this effect.

Use problem-cluster intervals for stability and correctness, with the numerator and
denominator recomputed in each resample. Report resamples with undefined estimates;
never silently convert them to zero. Few clusters require descriptive interpretation;
no narrow interval or power claim is justified from the current 11 problems.
McNemar is appropriate only for a prespecified pair of binary outcomes per independent
unit, not pooled repeated calls. Kappa, ordinal analyses, cluster bootstrap computation
and multiplicity corrections remain future implementation. Undefined degenerate kappa
must remain undefined. RQ5 subgroup analyses are exploratory with prespecified correction.

## Prompt conditions

### Generic rubric

> Determine whether the proposed solution is correct. Return only CORRECT or INCORRECT.

### Generic paraphrase

> Assess the answer's correctness. Respond with exactly one label: CORRECT or INCORRECT.

### Physics-specific rubric

> Evaluate every physical and mathematical step, including assumptions, units, signs, and whether the conclusion follows. Return only CORRECT if the entire reasoning is valid; otherwise return INCORRECT.

### Physics-specific paraphrase

> Check the derivation for physical or mathematical errors, omitted conditions, dimensional problems, and unsupported inferences. Label it CORRECT only when all essential reasoning is sound; otherwise label it INCORRECT.

Prompt equivalence must be independently reviewed before the sweep. The generic pair and physics-specific pair test paraphrase stability within condition. Generic versus physics-specific is an intervention and must not be called a paraphrase comparison.

## Repeatability and annotation controls

Add same-prompt repeat calls in fresh contexts with identical settings and content;
estimate their disagreement separately from paraphrase disagreement. Temperature zero
does not guarantee identical provider outputs. Randomize or counterbalance call order,
interleave conditions, and retain timestamps to reduce drift confounding. Counts and
schedule must be frozen and included in the eventual cost estimate.

Two independent physics annotators should label answer correctness, reasoning validity,
error type and rationale without model judgments. Retain individual annotations and
review dates. Adjudicate disagreements with a documented rationale; unresolved items
stay out of confirmation. Independently review within-rubric semantic equivalence.
The generic answer/solution wording and physics 'every step'/'essential reasoning'
wording may differ in intent; these are draft prompts pending review, not validated
paraphrases. Between-rubric comparisons are interventions.

## Development, freezing and replication

The 12 fixtures are development-only, version 0.2.0-dev, all provisional. The next
proposed matched design is documented in data_card.md and has not been generated.
Split development and confirmation by underlying problem_id before tuning prompts.
Do not select prompts after observing confirmatory outcomes. Freeze dataset hashes,
item selection, prompt texts, parser, code revision, endpoint definitions and stopping
rules before confirmation. Use a new version for revisions; preserve old artifacts.

Historical arXiv paper v2 is not rebuilt dataset v2. Consult upstream ERRATA.md and
pin repository and dataset commits before replication. Proposed first target is an
offline recomputation of corrected coherence outputs, then a small approved live
subset with documented departures. Do not copy historical numerical claims onto the
rebuilt sample. Upstream reported settings and decoding behavior need artifact-level
verification; no model or live configuration is selected in this milestone.

## Future execution requirements — not implemented

No key access or LLM calls are part of this milestone. Before paid work: disclose
model, scheduled calls including controls/retries, token estimates and maximum cost;
obtain explicit approval even for a paid smoke test. Implement a fail-closed maximum
budget guard before every attempt. A larger sweep needs separate explicit approval.

Keep raw generation immutable and separate from versioned parsed data and reports.
Use new timestamped run directories and refuse overwrites. Record provider, exact model,
UTC time, requested/actual temperature, seed support, token limits, prompt version,
item/problem IDs, full raw response, parsed label/status/parser version, retry attempts,
estimated/actual token usage and estimated cost with pricing source/date. Unsupported
parameters need an explicit not_supported status; unavailable actual usage is null,
not zero. Never include secrets in manifests or logs. Future release of reviewed raw
outputs is deliberate; local results are not automatically publication artifacts.
