"""Synthetic unit fixtures only; optional cached-release integration never downloads."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reproduction", ROOT / "scripts/reproduce_judgesense_coherence.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)


def fixture():
    d = dict(pair_id="p1", item_id="cohe_summeval_1_0", prompt_pair_id="cohe_summeval_1_0#T1-T2",
        task_type="coherence", ground_truth_label="3", ground_truth_raw=3.0, builder_version="2.0.0",
        template_a="T1", template_b="T2", prompt_a="synthetic prompt a", prompt_b="synthetic prompt b",
        response_being_judged="synthetic unit fixture", source=dict(source_dataset="mteb/summeval",
        source_split="test", loader_version="2.1.0", source_record_id="test[1].machine_summaries[0]",
        retrieved_at="2026-08-22T00:00:00+00:00"))
    r = {k: d[k] for k in ("pair_id", "item_id", "prompt_pair_id", "task_type", "ground_truth_label")}
    r.update(model="claude-haiku", budget_policy="matched", max_tokens=1024, error=None, ts="2026-08-22T01:00:00+00:00")
    for arm in ("a", "b", "a_repeat", "b_repeat"):
        r["decision_"+arm] = "3"
        r["prompt_"+arm+"_raw"] = "not reparsed: synthetic text"
        r["usage_"+arm] = dict(model_id=rp.MODEL, model_served=rp.MODEL, provider="anthropic", error=None,
            finish_reason="end_turn", decoding=dict(temperature=0, max_tokens=1024, system_prompt_sha="25972df1c2c4"))
    return d, r


def records(pairs):
    return [dict(item_id=str(i), decision_a=a, decision_b=b) for i, (a,b) in enumerate(pairs)]


class ReproductionTests(unittest.TestCase):
    def test_schema_and_preserved_provenance(self):
        d,r = fixture()
        joined = rp.validate([d], [r], 1)
        self.assertEqual(joined[0]["dataset_provenance"], d)
        self.assertEqual(joined[0]["prompt_a_raw"], r["prompt_a_raw"])
        self.assertEqual(joined[0]["source_document_id"], "summeval_test_1")

    def test_revision_mismatch(self):
        for key in ("pair_id", "item_id", "prompt_pair_id", "ground_truth_label"):
            d,r = fixture(); r[key] = "wrong"
            with self.subTest(key=key), self.assertRaises(ValueError): rp.validate([d],[r],1)

    def test_missing_field(self):
        d,r = fixture(); del r["decision_a"]
        with self.assertRaises(ValueError): rp.validate([d],[r],1)

    def test_wrong_model_configuration(self):
        for key,value in [("model_id","wrong"),("model_served","wrong"),("finish_reason","refusal")]:
            d,r=fixture(); r["usage_a"][key]=value
            with self.subTest(key=key), self.assertRaises(ValueError): rp.validate([d],[r],1)
        d,r=fixture(); r["budget_policy"]="native"
        with self.assertRaises(ValueError): rp.validate([d],[r],1)

    def test_unknown_label_and_type(self):
        for bad in ("7", 3, [], True):
            d,r=fixture(); r["decision_a"]=bad
            with self.subTest(bad=bad), self.assertRaises(ValueError): rp.validate([d],[r],1)

    def test_duplicates_and_empty(self):
        d,r=fixture()
        with self.assertRaises(ValueError): rp.validate([d,d],[r,r],2)
        with self.assertRaises(ValueError): rp.validate([],[],0)

    def test_unclear_allowed_without_text_parsing(self):
        d,r=fixture(); r["decision_a"]="UNCLEAR"
        m=rp.metrics(rp.validate([d],[r],1))
        self.assertEqual(m["invalid_incomplete_pairs"],1)
        self.assertEqual(m["strict_jss"],0)
        self.assertIsNone(m["valid_pair_jss"])

    def test_known_metrics(self):
        m=rp.metrics(records([("1","1"),("1","2"),("2","2"),("2","1")]))
        self.assertEqual(m["valid_pair_jss"],.5)
        self.assertEqual(m["cohens_kappa"],0)
        self.assertEqual(m["quadratic_weighted_kappa"],0)
        self.assertEqual(m["mean_absolute_rating_difference"],.5)

    def test_ordinal_distance(self):
        m=rp.metrics(records([("1","1"),("3","4"),("5","5")]))
        self.assertAlmostEqual(m["quadratic_weighted_kappa"],16/17)
        self.assertAlmostEqual(m["mean_absolute_rating_difference"],1/3)

    def test_invalid_denominators(self):
        m=rp.metrics(records([("1","1"),("UNCLEAR","UNCLEAR"),(None,"2")]))
        self.assertEqual(m["strict_jss"],1/3)
        self.assertEqual(m["valid_pair_jss"],1)
        self.assertEqual(m["valid_pair_disagreements"],0)
        self.assertEqual(m["invalid_outputs"],3)
        self.assertIsNone(m["cohens_kappa"])
        self.assertIsNone(rp.metrics([])["strict_jss"])

    def test_cluster_resampling_preserves_groups(self):
        rows=records([("1","1"),("2","3")])
        for r in rows: r["item_id"]="shared"
        ci=rp.bootstrap(rows,"item_id",50)
        self.assertEqual(ci["n_clusters"],1)
        self.assertEqual(ci["intervals"]["strict_jss"]["ci95"],[.5,.5])
        self.assertEqual(ci,rp.bootstrap(rows,"item_id",50))

    def test_undefined_resamples(self):
        ci=rp.bootstrap(records([("1","1")]),"item_id",10)
        self.assertEqual(ci["intervals"]["cohens_kappa"]["undefined_resamples"],10)
        self.assertIsNone(ci["intervals"]["cohens_kappa"]["ci95"])

    def test_checksum_fail_closed(self):
        with self.assertRaises(ValueError): rp.verify_bytes(b"changed",hashlib.sha256(b"original").hexdigest(),"fixture")
        self.assertEqual(rp.verify_bytes(b"ok",hashlib.sha256(b"ok").hexdigest(),"fixture"),b"ok")

    def test_retrieval_never_downloads_implicitly(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): rp.retrieve({"files":{"missing":{"sha256":"x"}}},Path(d))

    def test_bad_json_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x"; p.write_text('{broken',encoding="utf-8")
            with self.assertRaises(ValueError): rp.read_jsonl(p)

    def test_pinned_release_if_cached(self):
        lock=json.loads(rp.LOCK.read_text(encoding="utf-8"))
        cache=ROOT/"results/raw/judgesense"/lock["upstream_commit"]
        if not (cache/rp.RAW).exists(): self.skipTest("Retrieve checksum-pinned public release to run integration test")
        rp.retrieve(lock,cache)
        rows=rp.validate(rp.read_jsonl(cache/rp.DATA),rp.read_jsonl(cache/rp.RAW))
        m=rp.metrics(rows)
        self.assertEqual((m["n_rows"],m["agreements"],m["valid_pair_disagreements"]),(250,198,52))
        ci=rp.bootstrap(rows,"item_id")
        upstream=json.loads((cache/rp.SUMMARY).read_text(encoding="utf-8"))["claude-haiku"]["coherence"]
        self.assertTrue(all(v["match_at_upstream_precision"] for v in rp.compare(m,ci,upstream).values()))
