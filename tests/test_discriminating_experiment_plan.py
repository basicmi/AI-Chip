import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_discriminating_experiment_plan import build_plan


def fixtures():
    catalog = json.loads((Path(__file__).resolve().parents[1] / "data/performance-hypothesis-catalog.json").read_text())
    comparison = {
        "report_type": "performance_hypothesis_comparison",
        "record_id": "fixture",
        "overall_verdict": "undetermined",
        "ranking": "none",
        "hypotheses": [
            {"hypothesis_id": h["hypothesis_id"], "title": h["title"],
             "evidence_state": "no_direct_diagnostic_evidence"}
            for h in catalog["hypotheses"]
        ]
    }
    return comparison, catalog


class DiscriminatingExperimentPlannerTests(unittest.TestCase):
    def test_builds_pairwise_discrimination_plan(self):
        comparison, catalog = fixtures()
        plan = build_plan(comparison, catalog)
        self.assertEqual(plan["hypothesis_count"], 6)
        self.assertEqual(plan["hypothesis_pair_count"], 15)
        self.assertGreater(plan["measurement_count"], 0)
        self.assertEqual(plan["execution"]["status"], "proposal_only")
        self.assertEqual(plan["decision"]["hypothesis_verdict"], "undetermined")

    def test_greedy_plan_covers_pairs_for_declared_catalog(self):
        comparison, catalog = fixtures()
        plan = build_plan(comparison, catalog)
        self.assertTrue(plan["coverage_complete"])
        self.assertEqual(plan["uncovered_pairs"], [])
        self.assertTrue(all(p["selected_discriminating_measurements"]
                            for p in plan["pairwise_discrimination"]))

    def test_measurements_are_deduplicated_and_cost_is_explained(self):
        comparison, catalog = fixtures()
        plan = build_plan(comparison, catalog)
        descriptions = [m["description"].casefold() for m in plan["measurements"]]
        self.assertEqual(len(descriptions), len(set(descriptions)))
        self.assertTrue(all(m["relative_cost"]["basis"] for m in plan["measurements"]))

    def test_limit_exposes_uncovered_pairs_instead_of_hiding_them(self):
        comparison, catalog = fixtures()
        plan = build_plan(comparison, catalog, limit=1)
        self.assertFalse(plan["coverage_complete"])
        self.assertTrue(plan["uncovered_pairs"])

    def test_invalid_comparison_and_catalog_rejected(self):
        comparison, catalog = fixtures()
        with self.assertRaises(ValueError):
            build_plan({**comparison, "overall_verdict": "supported"}, catalog)
        with self.assertRaises(ValueError):
            build_plan(comparison, {"schema_version": "2.0", "hypotheses": []})

    def test_single_hypothesis_is_not_comparable(self):
        comparison, catalog = fixtures()
        comparison["hypotheses"] = comparison["hypotheses"][:1]
        with self.assertRaises(ValueError):
            build_plan(comparison, catalog)


if __name__ == "__main__":
    unittest.main()
