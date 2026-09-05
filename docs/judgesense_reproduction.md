# Offline JudgeSense coherence reproduction

This milestone recomputes a corrected released Haiku result, not a live replication.
It reads existing decision_a/decision_b labels without parsing raw text into new labels.
The source lock pins Git commit 223c31d991ef547ea07d81bba054e6973245a8dc and full SHA-256 checksums.

## Run

Requires Python >=3.10 and NumPy >=1.24. The recorded run used Python 3.14 and NumPy
2.5.2; the generated manifest records exact runtime versions. Install the optional
reproduction extra if needed (pip install -e ".[reproduction]"). No model SDK is used.

From the project root, retrieve public files once and analyze into a NEW directory:

    python scripts/reproduce_judgesense_coherence.py --download --output-dir results/raw/my_reproduction_01

Then rerun without any network access, using the verified cache:

    python scripts/reproduce_judgesense_coherence.py --output-dir results/raw/my_reproduction_02

Existing output directories and checksum mismatches cause a clear failure. The cache
defaults to results/raw/judgesense/<commit>. Raw files, copied upstream code and joined
provenance stay ignored. Upstream code is inspected but never imported or executed.
All generated run outputs include metrics.json, manifest.json, report.md and
joined_provenance.jsonl. Promote the small report/metrics/manifest for review only;
retain the full joined source and raw outputs locally. No authentication is required.

## Matching evidence

The 250 pair IDs, item IDs, prompt-pair IDs, task and gold labels join exactly.
The dataset file at raw-release commit 5e34e13a3d0715a1db245f8240229fd002de8633 is
byte-identical to the pinned dataset. The latest dataset change is
818bff0b781fe5ad04bfdaea3212ba0b00ea0825, before the logged run timestamps.
The runner reads data/v2/coherence.jsonl and copies those IDs. Every logged arm,
including repeats, names claude-haiku-4-5-20251001 as requested and served model.
No prompt-input hash is logged: linkage is supported by artifacts and history, not
cryptographic evidence of what the provider saw. This is disclosed rather than
inferred from filenames alone. The lock records file hashes rather than relying on
ambiguous v2 terminology: current card says v2.1; builder says 2.0.0; loader says 2.1.0.

## Statistics and comparison

Item-cluster bootstrap follows the upstream sampling convention: insertion-order
clusters, NumPy default_rng(42), 2000 resamples, percentile 2.5/97.5 with linear
interpolation. Source-document bootstrap is an additional sensitivity analysis for
92 documents shared by 250 summaries. Repeats are retained, not counted as new items.
Kappa and ordinal metrics use valid pairs only; strict JSS counts invalid pairs as
failures. Unknown decision tokens, transport errors, refusals, revisions, duplicate
IDs and mixed configurations fail closed for explicit review. Null/UNCLEAR decisions
are supported. No parsing failure is counted as an observed verdict flip.

Upstream summary rounds to four decimals. Comparison checks this precision and the
reported JSS interval. Mean absolute rating difference and extra confidence intervals
have no reported upstream comparison target. Undefined ratios remain null; undefined
bootstrap resample counts are exposed. No scientific correctness is inferred.

## Attribution and licensing

Reference: Bellibatlu, Raff and Zhang, JudgeSense, https://arxiv.org/abs/2604.23478 .
Code/artifacts: https://github.com/rohithreddybc/judgeSense at the pinned commit.
Implementation is independent standard metric code; cluster-bootstrap conventions
are adapted from upstream src/metrics_v2.py (MIT). Its copyright/license notice is
preserved in third_party/JudgeSense_LICENSE.txt. The upstream dataset card declares
CC-BY-4.0; underlying SummEval/source terms remain applicable. No raw dataset is
redistributed in the proposed commit. Cache retrieval also preserves upstream LICENSE
and data documentation. This project is unaffiliated with the upstream authors.
