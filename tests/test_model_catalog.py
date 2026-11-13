import copy
import json
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_model_catalog import validate_catalog

catalog = json.loads((ROOT / "data/model-catalog.json").read_text())
support = json.loads((ROOT / "data/model-support.json").read_text())
TODAY = date(2026, 11, 13)


class ModelCatalogTests(unittest.TestCase):
    def test_catalog_is_valid_without_synthesizing_support_paths(self):
        self.assertEqual(validate_catalog(catalog, support, today=TODAY), [])
        support_ids = {p["model_id"] for p in support["support_paths"]}
        catalog_only = [m for m in catalog["models"] if m["id"] not in support_ids]
        self.assertGreaterEqual(len(catalog_only), 6)
        self.assertEqual(len(support["support_paths"]), 12)

    def test_rejects_missing_supported_model(self):
        data = copy.deepcopy(catalog)
        data["models"] = [m for m in data["models"] if m["id"] != "gpt-oss-120b"]
        self.assertTrue(any("every supported model" in e for e in validate_catalog(data, support, today=TODAY)))

    def test_rejects_duplicate_model_repo_or_id(self):
        data = copy.deepcopy(catalog)
        data["models"].append(copy.deepcopy(data["models"][0]))
        errors = validate_catalog(data, support, today=TODAY)
        self.assertTrue(any("duplicated" in e for e in errors))
        self.assertTrue(any("unique and nonempty" in e for e in errors))

    def test_rejects_future_review_date(self):
        data = copy.deepcopy(catalog)
        data["models"][0]["catalog_checked_at"] = "2099-01-01"
        self.assertTrue(any("in the future" in e for e in validate_catalog(data, support, today=TODAY)))

    def test_rejects_invalid_access_and_context(self):
        data = copy.deepcopy(catalog)
        data["models"][0]["access"] = "guaranteed_deployable"
        data["models"][0]["context_length_tokens"] = -1
        errors = validate_catalog(data, support, today=TODAY)
        self.assertTrue(any("access is invalid" in e for e in errors))
        self.assertTrue(any("context_length_tokens" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
