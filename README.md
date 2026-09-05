# Are LLM Judges Reliable Evaluators of Physics Reasoning?

**A Study of Prompt Sensitivity and Scientific Correctness**

This independent project aims to replicate one core result from [JudgeSense](https://arxiv.org/abs/2604.23478)—that an LLM judge's decision can change under semantically equivalent evaluation prompts—and extend it to physics reasoning.

This project is not affiliated with, endorsed by, or maintained by the JudgeSense authors. The upstream paper and repository are research references; no replication results have been collected yet.

The extension separates two properties that must not be confused:

1. **Stability:** Does the judge give the same verdict when only the rubric wording changes?
2. **Correctness:** Does the verdict agree with a physics expert label?

A judge can be perfectly stable and consistently wrong. We therefore report both.

## Current milestone: study foundation

The first milestone is deliberately offline and inexpensive. It provides:

- a draft study protocol in `docs/study_protocol.md`;
- a small schema-valid pilot set of controlled physics solutions;
- implementations of prompt-pair agreement (JSS), flip rate, accuracy, and joint reliability categories;
- tests that verify the metric behavior, including the “stable but wrong” failure mode;
- a local baseline command that requires no API key and spends no money.

## Research questions

- **RQ1:** How stable are judge verdicts under semantically equivalent rubric paraphrases?
- **RQ2:** How accurately do judge verdicts identify physics reasoning errors?
- **RQ3:** Does a correct final answer make a judge less likely to detect invalid reasoning?
- **RQ4:** Do physics-specific rubrics improve correctness or stability relative to generic rubrics?

## Quick start

Requires Python 3.10 or newer.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -e .
python -m unittest discover -s tests
python -m physics_judge.baseline
```

The baseline uses deterministic mock judgments to demonstrate the full scoring contract. It does **not** claim empirical results about any LLM.

## Planned phases

1. **Offline foundation (complete):** schema, metrics, pilot items, tests, and protocol.
2. **Replication:** run a small JudgeSense factuality/coherence subset and verify the qualitative prompt-sensitivity finding.
3. **Physics pilot:** obtain judgments for controlled physics solutions using frozen prompts and model settings.
4. **Extension:** compare generic versus physics-specific rubrics and test correct-answer/wrong-reasoning cases.
5. **Scale and report:** expand only after power, cost, and annotation checks.

## Repository layout

```text
data/physics_pilot.jsonl       Controlled pilot items and expert labels
docs/study_protocol.md         Draft hypotheses and analysis plan
src/physics_judge/metrics.py   Reliability metrics
src/physics_judge/baseline.py  Offline end-to-end demonstration
tests/                         Metric and data-contract tests
```

## Reproducibility principles

- Preserve raw model responses; parse them in a separate step.
- Record model identifier, provider, date, temperature, seed when available, and prompt version.
- Estimate cost before every API sweep.
- Freeze the pilot dataset before examining model results.
- Treat prompt equivalence as a human-validated experimental assumption.
- Never interpret JSS alone as evidence of scientific correctness.

## References

- Bellibatlu, Raff, and Zhang (2026), [JudgeSense: A Benchmark for Prompt Sensitivity in LLM-as-a-Judge Systems](https://arxiv.org/abs/2604.23478).
- Official upstream code: [rohithreddybc/judgeSense](https://github.com/rohithreddybc/judgeSense).

## Status

Research scaffold only. No live LLM results have been collected yet.
