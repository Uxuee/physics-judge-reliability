"""Offline reproduction from released decisions; never imports a model client.

Independent implementation of standard agreement formulas. Bootstrap sampling follows
JudgeSense metrics_v2.py's item order, NumPy default_rng(42), 2000 resamples and
percentile convention for comparability. See docs/judgesense_reproduction.md.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.request import urlopen

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LOCK = Path(__file__).with_name("judgesense_coherence_sources.json")
DATA = "data/v2/coherence.jsonl"
RAW = "data/results_v2/raw/claude-haiku_coherence.jsonl"
SUMMARY = "data/results_v2/metrics_summary.json"
LABELS = {"1", "2", "3", "4", "5"}
MODEL = "claude-haiku-4-5-20251001"
RATE_KEYS = ("output_coverage", "pair_coverage", "strict_jss", "valid_pair_jss",
             "valid_pair_disagreement_rate", "cohens_kappa", "quadratic_weighted_kappa",
             "mean_absolute_rating_difference")


def verify_bytes(content, expected, name):
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError(f"Checksum mismatch: {name}; refusing analysis")
    return content


def retrieve(lock, cache, download=False):
    """Network only with explicit --download; immutable commit URLs, no credentials."""
    for name, spec in lock["files"].items():
        target = cache / name
        if not target.exists():
            if not download:
                raise ValueError(f"Missing {name}; retrieve with --download first")
            url = f"https://raw.githubusercontent.com/rohithreddybc/judgeSense/{lock['upstream_commit']}/{name}"
            with urlopen(url, timeout=60) as response:
                content = response.read()
            verify_bytes(content, spec["sha256"], name)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(content)
        verify_bytes(target.read_bytes(), spec["sha256"], name)


def read_jsonl(path):
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{number}: malformed JSON") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path.name}:{number}: expected object")
        rows.append(value)
    return rows


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(dataset, raw, expected_rows=250):
    """Fail closed on revision joins/configuration; do not reparse response text."""
    require(len(dataset) == len(raw) == expected_rows, "Unexpected dataset/raw row count")
    require(expected_rows > 0, "Empty release")
    for rows in (dataset, raw):
        for key in ("pair_id", "item_id", "prompt_pair_id"):
            require(all(type(r.get(key)) is str and r[key] for r in rows), f"Missing/string {key}")
            require(len({r[key] for r in rows}) == expected_rows, f"Duplicate {key}; review retry/revision semantics")
    index = {r["pair_id"]: r for r in dataset}
    require(set(index) == {r["pair_id"] for r in raw}, "Pair sets differ")
    joined = []
    for r in raw:
        d = index[r["pair_id"]]
        for key in ("item_id", "prompt_pair_id", "task_type", "ground_truth_label"):
            require(r.get(key) == d.get(key), f"Revision mismatch: {r['pair_id']} {key}")
        require(d.get("task_type") == "coherence", "Wrong task")
        require(d.get("ground_truth_label") in LABELS, "Invalid gold scale")
        require(type(d.get("ground_truth_raw")) in (int, float) and 1 <= d["ground_truth_raw"] <= 5, "Invalid raw gold")
        require(d.get("builder_version") == "2.0.0", "Unexpected builder revision")
        for key in ("prompt_a", "prompt_b", "response_being_judged", "template_a", "template_b"):
            require(type(d.get(key)) is str and d[key].strip(), f"Missing {key}")
        require(d["prompt_pair_id"] == d["item_id"] + "#" + d["template_a"] + "-" + d["template_b"], "Template identity mismatch")
        source = d.get("source", {})
        require(source.get("source_dataset") == "mteb/summeval" and source.get("source_split") == "test", "Wrong source")
        require(source.get("loader_version") == "2.1.0", "Wrong loader revision")
        match = re.fullmatch(r"test\[(\d+)\]\.machine_summaries\[(\d+)\]", source.get("source_record_id", ""))
        require(match is not None, "Invalid source record identity")
        require(d["item_id"] == f"cohe_summeval_{match[1]}_{match[2]}", "Source/item identity mismatch")
        require(r.get("model") == "claude-haiku" and r.get("budget_policy") == "matched" and r.get("max_tokens") == 1024, "Mixed model/budget")
        require(r.get("error") is None and "error" in r, "Transport error requires reviewed policy")
        require(datetime.fromisoformat(r["ts"]) >= datetime.fromisoformat(source["retrieved_at"]), "Run predates dataset")
        for arm in ("a", "b", "a_repeat", "b_repeat"):
            key = "decision_" + arm
            require(key in r and (r[key] is None or type(r[key]) is str and r[key] in LABELS | {"UNCLEAR"}), f"Unexpected released decision: {key}")
            require(type(r.get("prompt_" + arm + "_raw")) is str, "Missing released response text")
            usage = r.get("usage_" + arm, {})
            require(usage.get("model_id") == usage.get("model_served") == MODEL and usage.get("provider") == "anthropic", "Model identity mismatch")
            require(usage.get("error") is None and usage.get("finish_reason") == "end_turn", "Nonstandard call outcome requires review")
            decoding = usage.get("decoding", {})
            require(decoding.get("temperature") == 0 and decoding.get("max_tokens") == 1024 and decoding.get("system_prompt_sha") == "25972df1c2c4", "Decoding mismatch")
        joined.append({**r, "source_document_id": "summeval_test_" + match[1], "dataset_provenance": d})
    return joined


def metrics(rows):
    n = len(rows)
    pairs = [(r.get("decision_a"), r.get("decision_b")) for r in rows]
    valid = [(a, b) for a, b in pairs if a in LABELS and b in LABELS]
    v = len(valid)
    agree = sum(a == b for a, b in valid)
    divide = lambda a, b: a / b if b else None
    kappa = qwk = mad = None
    if v:
        ca, cb = Counter(a for a, _ in valid), Counter(b for _, b in valid)
        pe = sum(ca[k] * cb[k] for k in LABELS) / v**2
        kappa = divide(agree / v - pe, 1 - pe)
        observed = sum((int(a) - int(b))**2 for a, b in valid) / v
        expected = sum(ca[a] * cb[b] * (int(a) - int(b))**2 for a in LABELS for b in LABELS) / v**2
        qwk = 1 - observed / expected if expected else None
        mad = sum(abs(int(a) - int(b)) for a, b in valid) / v
    invalid_arms = sum(a not in LABELS for p in pairs for a in p)
    return {"n_rows": n, "n_items": len({r["item_id"] for r in rows}),
            "valid_pairs": v, "valid_outputs": 2*n-invalid_arms,
            "invalid_incomplete_pairs": n-v, "invalid_outputs": invalid_arms,
            "agreements": agree, "valid_pair_disagreements": v-agree,
            "output_coverage": divide(2*n-invalid_arms, 2*n), "pair_coverage": divide(v, n),
            "strict_jss": divide(agree, n), "valid_pair_jss": divide(agree, v),
            "valid_pair_disagreement_rate": divide(v-agree, v), "cohens_kappa": kappa,
            "quadratic_weighted_kappa": qwk, "mean_absolute_rating_difference": mad}


def bootstrap(rows, cluster_key, n_bootstrap=2000, seed=42):
    require(bool(rows) and n_bootstrap > 0, "Bootstrap requires rows and positive resample count")
    groups = {}
    for r in rows:
        require(cluster_key in r and bool(r[cluster_key]), "Missing cluster identity")
        groups.setdefault(r[cluster_key], []).append(r)
    clusters = list(groups.values())
    rng = np.random.default_rng(seed)
    estimates = {key: [] for key in RATE_KEYS}
    for _ in range(n_bootstrap):
        sample = [r for i in rng.integers(0, len(clusters), size=len(clusters)) for r in clusters[i]]
        m = metrics(sample)
        for key in RATE_KEYS:
            if m[key] is not None:
                estimates[key].append(m[key])
    return {"cluster_key": cluster_key, "n_clusters": len(clusters), "n_bootstrap": n_bootstrap,
            "seed": seed, "confidence": .95, "method": "percentile; NumPy default_rng; linear quantiles",
            "intervals": {key: {"ci95": [float(v) for v in np.percentile(values, [2.5, 97.5])] if values else None,
                                 "undefined_resamples": n_bootstrap-len(values)} for key, values in estimates.items()}}


def compare(m, ci, upstream):
    mapping = {"n_rows": "n_rows", "n_items": "n_items", "strict_jss": "jss_strict",
               "valid_pair_jss": "jss_on_parseable_pairs", "cohens_kappa": "chance_corrected_jss",
               "quadratic_weighted_kappa": "quadratic_weighted_kappa"}
    result = {k: {"recomputed": m[k], "upstream": upstream[v],
                  "match_at_upstream_precision": round(m[k], 4) == upstream[v]} for k, v in mapping.items()}
    result["strict_jss_ci95"] = {"recomputed": ci["intervals"]["strict_jss"]["ci95"], "upstream": upstream["ci95"],
        "match_at_upstream_precision": [round(x, 4) for x in ci["intervals"]["strict_jss"]["ci95"]] == upstream["ci95"]}
    result["malformed_rate"] = {"recomputed": 1-m["output_coverage"], "upstream": upstream["malformed_rate"],
        "match_at_upstream_precision": round(1-m["output_coverage"], 4) == upstream["malformed_rate"]}
    return result



def render_report(result, manifest):
    m = result["metrics"]
    lines = ["# JudgeSense coherence: offline reproduction", "",
             "Recomputed from released decisions; no live replication or new model calls.", "",
             "Upstream commit: " + manifest["upstream_commit"],
             "Model: " + manifest["model_id"],
             "Dataset: " + manifest["dataset_version"], "",
             "| Metric | Recomputed | Item-cluster 95% CI |", "| --- | ---: | --- |"]
    for key, value in m.items():
        ci = result["item_cluster_ci"]["intervals"].get(key, {}).get("ci95")
        lines.append(f"| {key} | {value} | {ci if ci is not None else 'not applicable'} |")
    lines += ["", "All compared corrected upstream values match at their reported precision: " + str(result["matches_upstream"]),
              "Counts, coverage, JSS and the JSS interval agree exactly. Kappas agree after rounding to four decimals.",
              "Mean absolute rating difference and kappa/MAD intervals are additional computations; the pinned summary supplies no comparison values for them.",
              "", "## Clustering and policy", "",
              "The upstream reproduction uses 250 item clusters, preserving input order, 2000 percentile resamples, NumPy default_rng seed 42.",
              "There are 92 source-document clusters. The source-document sensitivity interval for strict JSS is " + str(result["source_document_sensitivity_ci"]["intervals"]["strict_jss"]["ci95"]) + ".",
              "The latter allows dependence between different summaries of the same document; it is an additional analysis, not a claimed match to upstream.",
              "Primary A/B decisions are scored unchanged. Same-prompt repeats remain in provenance but are not pooled as independent pairs.",
              "Invalid pairs receive no strict-agreement credit and are excluded from valid-pair/kappa/ordinal denominators. No invalids, refusals or transport errors occur in this cell.",
              "The upstream regeneration code conditions on answered pairs; this does not alter this fully answered cell. Its last-write-wins retry logic is not exercised: IDs are unique.",
              "Undefined kappa is null here rather than upstream's zero convention; no observed or bootstrap estimate is degenerate in this run.",
              "Bootstrap [1,1] coverage intervals reflect this resample's all-valid data, not a guarantee of zero population failure probability.",
              "", "## Provenance and limits", "", manifest["provenance_evidence"],
              "The dataset last changed at " + manifest["dataset_last_changed"] + "; raw outputs last changed at " + manifest["raw_last_changed"] + ".",
              "Actual logged configuration is temperature 0, matched max_tokens 1024, system-prompt digest 25972df1c2c4. Registry native budget 20 is not the run's matched budget.",
              "No ground-truth accuracy claim follows from agreement. This result concerns one Haiku run and coherence summaries, not all models or physics reasoning.",
              "Prompt semantic equivalence remains an upstream scientific assumption, not established by this computation. Dataset card v2.1 and builder 2.0.0 are recorded separately.",
              "No historical v1 headline or mock baseline is used as a target.",
              "", "## Attribution", "",
              "[JudgeSense repository](" + manifest["upstream_repository"] + ") and [paper](https://arxiv.org/abs/2604.23478).",
              "Scoring is independently implemented; bootstrap conventions follow upstream metrics_v2.py. See docs/judgesense_reproduction.md and third_party/JudgeSense_LICENSE.txt.",
              "Raw files remain in ignored local storage and are retrieved by immutable URLs and SHA-256 checksums. No large raw artifact is proposed for commit.",
              "", "New model calls: 0. Key accessed: no. Cost: USD 0.", ""]
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--download", action="store_true", help="Retrieve missing public files, verify checksums")
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory; existing directories are refused")
    args = parser.parse_args()
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    cache = args.cache or ROOT / "results/raw/judgesense" / lock["upstream_commit"]
    require(not args.output_dir.exists(), "Output directory exists; choose a new run directory")
    retrieve(lock, cache, args.download)
    rows = validate(read_jsonl(cache / DATA), read_jsonl(cache / RAW))
    m = metrics(rows)
    item_ci = bootstrap(rows, "item_id")
    document_ci = bootstrap(rows, "source_document_id")
    upstream = json.loads((cache / SUMMARY).read_text(encoding="utf-8"))["claude-haiku"]["coherence"]
    comparison = compare(m, item_ci, upstream)
    result = {"metrics": m, "item_cluster_ci": item_ci, "source_document_sensitivity_ci": document_ci,
              "comparison": comparison, "matches_upstream": all(r["match_at_upstream_precision"] for r in comparison.values())}
    manifest = {**lock, "analysis_date": datetime.now(timezone.utc).isoformat(), "analysis_kind": "offline reproduction",
        "analysis_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_version": sys.version, "numpy_version": np.__version__, "clustering_unit": "item_id (upstream reproduction); source_document_id (sensitivity)",
        "metric_definitions": {"strict_jss": "valid agreements / all pairs", "valid_pair_jss": "agreements / valid pairs",
          "coverage": "valid outputs / 2N; valid pairs / N reported separately", "kappa": "(observed agreement - marginal expected agreement)/(1-expected)",
          "quadratic_weighted_kappa": "1 - observed squared rating distance / marginal expected squared distance",
          "mean_absolute_rating_difference": "mean abs(A-B) over valid pairs"},
        "malformed_output_policy": "Use released decisions unchanged; UNCLEAR/null invalid. Strict JSS gives no credit; valid-pair and ordinal metrics exclude invalid pairs. Invalid pairs are not verdict flips. Fail on transport/refusal or unknown labels pending policy review.",
        "repeat_policy": "Preserve repeat arms; do not add them as independent rows or reparaphrase observations",
        "provenance_evidence": "All 250 identity/gold joins agree; dataset bytes also match at raw_last_changed commit; dataset build precedes all run timestamps. No input-prompt hash in raw logs: linkage is artifact/history based, not cryptographic proof of provider inputs.",
        "undefined_policy": "null if denominator zero; report undefined bootstrap resamples; upstream uses zero for degenerate kappa but this run is nondegenerate",
        "new_model_calls": 0, "key_accessed": False, "cost_usd": 0}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for name, value in [("metrics.json", result), ("manifest.json", manifest)]:
        with (args.output_dir / name).open("x", encoding="utf-8") as f:
            json.dump(value, f, indent=2, allow_nan=False)
            f.write("\n")
    with (args.output_dir / "joined_provenance.jsonl").open("x", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (args.output_dir / "report.md").write_text(render_report(result, manifest), encoding="utf-8")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        raise SystemExit(f"Reproduction failed: {exc}") from exc
