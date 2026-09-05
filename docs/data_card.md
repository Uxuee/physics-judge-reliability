# Physics engineering fixtures

## Version and intended use

Dataset version: 0.2.0-dev. There are 12 candidate solutions over 11 underlying
problems. Use these fixtures to test validation, parsing and scoring offline.
They are development data, not publication data or a frozen confirmatory sample.
No real model results have been collected. Mock judgments do not measure LLM ability.

## Schema and annotation

Every record requires nonempty string fields: item_id, problem_id, level, domain,
question, candidate_solution, expert_label, expert_rationale, error_type,
dataset_version, source_notes, annotation_status. reasoning_valid and
final_answer_correct must be JSON booleans (not strings or integers).

item_id identifies a candidate solution; problem_id groups solutions to exactly the
same question, domain and level. gr_001 and gr_002 share kerr_horizon. gr_004 asks a
different question and therefore has a different problem_id.

expert_label is CORRECT exactly when reasoning_valid AND final_answer_correct;
otherwise it is INCORRECT. error_type is none exactly for CORRECT items. Reasoning
validity assesses all essential steps; a mostly correct method with a calculation
error is not fully valid reasoning. An otherwise valid derivation with a wrongly
transcribed final answer may have reasoning_valid=true and final_answer_correct=false;
reviewers must explain that distinction. Multiple substantive errors require notes.

Allowed levels: undergraduate, advanced. Allowed annotation statuses:

- provisional: no completed independent review is claimed.
- independently_reviewed: two independent annotations agree, with retained evidence.
- adjudicated: disagreement has been resolved and the resolution is documented.

All 12 current records are provisional. Existing expert_label values are provisional
scaffold labels, not evidence of expert certification. The validator checks the
status vocabulary, not whether review actually occurred. It cannot certify physics.
source_notes contain derivation notes or references to verify, not invented source
attribution or a claim that the examples were drawn from an external benchmark.

## Coverage and limitations

Eight undergraduate items cover mechanics (2), electromagnetism (2), thermodynamics
(1), quantum mechanics (1), special relativity (1), and dimensional analysis (1).
Four advanced items cover general relativity. Six labels are CORRECT and six are
INCORRECT. All correct items have valid reasoning and correct answers; all incorrect
items currently have invalid reasoning and incorrect answers. H2 is untestable here.

Current error types: none, vector_direction, invalid_integration,
missing_relativistic_dynamics, domain_error, overgeneralization, unit_inconsistency.
Most incorrect categories contain only one item. This is not balanced domain,
difficulty or error-type coverage. Most examples test conceptual recognition, not
long derivation checking. Advanced language can cue the answer. Domain membership
is not a validated difficulty measurement.

The Kerr units are G=c=1, M>0 and a=J/M. The extremal orbit item concerns a limit of
Boyer-Lindquist radii, not physical coincidence with the horizon. The entropy item
is restricted to macroscopic thermodynamics. Such qualifications require expert review.

Before scientific use, obtain two independent, model-output-blinded physics reviews
of each item and rubric pair, retain individual rationales, adjudicate disagreements,
and exclude unresolved items. Do not infer human review from this file or passing tests.

## Next proposed dataset milestone — not implemented

Consider six undergraduate problems, each with three matched candidate solutions:

1. Valid reasoning and a correct final answer.
2. Invalid reasoning but a correct final answer.
3. Invalid reasoning and an incorrect final answer.

The same question and problem_id must be retained within each triplet. Match error
severity, length and presentation as closely as practical, and document unavoidable
differences. This proposed 18-item design is necessary for a controlled H2 pilot,
but matching alone does not establish causality. The current four advanced fixtures
would remain exploratory. No triplets have been manufactured or validated here.
Select error categories and review procedures with the researcher before authoring.
Development and confirmatory partitions must be disjoint at problem_id level.
