# Study protocol (draft preregistration)

## Aim

Test whether LLM judges are both stable under semantically equivalent rubric wording and correct against expert physics labels.

## Confirmatory hypotheses

- **H1 — Prompt sensitivity:** At least one tested judge/rubric condition has a non-zero verdict flip rate across equivalent prompt pairs.
- **H2 — Final-answer bias:** Error-detection recall is lower for invalid derivations that end with the correct final answer than for invalid derivations with an incorrect final answer.
- **H3 — Domain rubric:** A physics-specific rubric improves error-detection accuracy over a generic correctness rubric.
- **H4 — Stability is insufficient:** Some judgments fall in the stable-but-wrong category, demonstrating that JSS alone is not a correctness measure.

H1 is a replication target. H2–H4 are the extension.

## Unit of analysis

The primary unit is one candidate physics solution. Each solution is judged under a paired set of semantically equivalent instructions. Repeated runs and additional paraphrase pairs remain clustered within the solution; they are not treated as independent observations.

## Dataset design

The pilot will contain balanced strata across:

- expert label: correct / incorrect;
- final answer: correct / incorrect;
- reasoning: valid / invalid;
- level: undergraduate / advanced;
- error type: sign, units, missing condition, invalid inference, arithmetic, overgeneralization, and correct-answer/wrong-reasoning.

Every item must include an expert rationale. Advanced items should be independently checked by a second physicist before inclusion in confirmatory analysis. Pilot items may be revised only before the dataset is frozen.

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

## Primary outcomes

- JSS (paired-prompt raw agreement)
- flip rate, `1 - JSS`
- expert-label accuracy for each prompt arm
- incorrect-solution recall (error-detection sensitivity)
- stable-correct, stable-wrong, and unstable proportions

Secondary outcomes may include Cohen's kappa, bootstrap confidence intervals clustered by item, performance by error type, and malformed-output rate.

## Minimal replication

Before collecting physics results:

1. Use a frozen subset of the released JudgeSense v2 factuality and coherence data.
2. Run one affordable judge model at the authors' reported decoding settings where supported.
3. Recompute JSS/flip rate from raw decisions.
4. Compare the qualitative direction, not demand exact equality across model versions or providers.
5. Document every departure from the upstream protocol.

## Pilot size and stopping rule

Begin with 12–20 items and one model solely to test parsing, costs, and obvious ceiling/floor effects. Do not treat this as publication evidence. Freeze the full design and perform a power analysis before scaling. Stop an API sweep automatically if estimated spend exceeds its configured budget.

## Analysis safeguards

- Analyze temperature-zero repeatability separately from paraphrase sensitivity.
- Do not silently drop malformed labels; report them and count them as failures in the strict analysis.
- Do not select prompts after seeing which produce the preferred result.
- Report model version/date because hosted models can change.
- Correct for multiple comparisons in exploratory per-error-type analyses.
- Release raw outputs where provider policy permits.

## What would count as a meaningful contribution?

Simply replacing a general benchmark with physics questions is insufficient. A stronger contribution needs controlled error types, expert labels, explicit separation of stability from correctness, and a tested mechanism such as correct-final-answer bias or rubric specificity.
