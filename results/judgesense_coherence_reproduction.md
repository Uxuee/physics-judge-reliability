# JudgeSense coherence: offline reproduction

Recomputed from released decisions; no live replication or new model calls.

Upstream commit: 223c31d991ef547ea07d81bba054e6973245a8dc
Model: claude-haiku-4-5-20251001
Dataset: v2.1 (dataset card); builder_version 2.0.0; loader_version 2.1.0

| Metric | Recomputed | Item-cluster 95% CI |
| --- | ---: | --- |
| n_rows | 250 | not applicable |
| n_items | 250 | not applicable |
| valid_pairs | 250 | not applicable |
| valid_outputs | 500 | not applicable |
| invalid_incomplete_pairs | 0 | not applicable |
| invalid_outputs | 0 | not applicable |
| agreements | 198 | not applicable |
| valid_pair_disagreements | 52 | not applicable |
| output_coverage | 1.0 | [1.0, 1.0] |
| pair_coverage | 1.0 | [1.0, 1.0] |
| strict_jss | 0.792 | [0.74, 0.84] |
| valid_pair_jss | 0.792 | [0.74, 0.84] |
| valid_pair_disagreement_rate | 0.208 | [0.16, 0.26] |
| cohens_kappa | 0.6227619627985259 | [0.5343529585406661, 0.7062472316437237] |
| quadratic_weighted_kappa | 0.8593523045764203 | [0.8139792351200766, 0.8966374151852512] |
| mean_absolute_rating_difference | 0.212 | [0.16, 0.264] |

All compared corrected upstream values match at their reported precision: True
Counts, coverage, JSS and the JSS interval agree exactly. Kappas agree after rounding to four decimals.
Mean absolute rating difference and kappa/MAD intervals are additional computations; the pinned summary supplies no comparison values for them.

## Clustering and policy

The upstream reproduction uses 250 item clusters, preserving input order, 2000 percentile resamples, NumPy default_rng seed 42.
There are 92 source-document clusters. The source-document sensitivity interval for strict JSS is [0.7427290764463933, 0.8427976877645602].
The latter allows dependence between different summaries of the same document; it is an additional analysis, not a claimed match to upstream.
Primary A/B decisions are scored unchanged. Same-prompt repeats remain in provenance but are not pooled as independent pairs.
Invalid pairs receive no strict-agreement credit and are excluded from valid-pair/kappa/ordinal denominators. No invalids, refusals or transport errors occur in this cell.
The upstream regeneration code conditions on answered pairs; this does not alter this fully answered cell. Its last-write-wins retry logic is not exercised: IDs are unique.
Undefined kappa is null here rather than upstream's zero convention; no observed or bootstrap estimate is degenerate in this run.
Bootstrap [1,1] coverage intervals reflect this resample's all-valid data, not a guarantee of zero population failure probability.

## Provenance and limits

All 250 identity/gold joins agree; dataset bytes also match at raw_last_changed commit; dataset build precedes all run timestamps. No input-prompt hash in raw logs: linkage is artifact/history based, not cryptographic proof of provider inputs.
The dataset last changed at 818bff0b781fe5ad04bfdaea3212ba0b00ea0825; raw outputs last changed at 5e34e13a3d0715a1db245f8240229fd002de8633.
Actual logged configuration is temperature 0, matched max_tokens 1024, system-prompt digest 25972df1c2c4. Registry native budget 20 is not the run's matched budget.
No ground-truth accuracy claim follows from agreement. This result concerns one Haiku run and coherence summaries, not all models or physics reasoning.
Prompt semantic equivalence remains an upstream scientific assumption, not established by this computation. Dataset card v2.1 and builder 2.0.0 are recorded separately.
No historical v1 headline or mock baseline is used as a target.

## Attribution

[JudgeSense repository](https://github.com/rohithreddybc/judgeSense) and [paper](https://arxiv.org/abs/2604.23478).
Scoring is independently implemented; bootstrap conventions follow upstream metrics_v2.py. See docs/judgesense_reproduction.md and third_party/JudgeSense_LICENSE.txt.
Raw files remain in ignored local storage and are retrieved by immutable URLs and SHA-256 checksums. No large raw artifact is proposed for commit.

New model calls: 0. Key accessed: no. Cost: USD 0.
