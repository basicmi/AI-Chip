import unittest
from test_performance_evidence_review import fixture
from review_performance_experiment_evidence import build_review,digest
from append_performance_review_decision import append_decision,CHECKS
from extract_performance_knowledge import extract_knowledge,build_catalog


def prepared(verdict="supported"):
    record,plan,submission=fixture()
    report=build_review(record,plan,submission)
    decision={"decision_id":"human-1","reviewer":"reviewer-a",
      "reviewed_at":"2026-11-26T00:00:00Z","review_sha256":digest(report),
      "verdict":verdict,"rationale":"Reviewed source and counter evidence; observed treatment effect is consistent with the stated mechanism.",
      "applicability":"Only the declared model, ISL, fixed context and decode TP values.",
      "limitations":"Synthetic fixture; no claim beyond these conditions.",
      "supersedes":None,"checks":dict.fromkeys(CHECKS,True),
      "evidence_run_ids":[run["run_id"] for run in submission["runs"]]}
    ledger=append_decision({"schema_version":"1.0","entries":[]},
                           record,plan,submission,decision)
    return record,plan,submission,report,ledger


class PerformanceKnowledgeTests(unittest.TestCase):
    def test_extract_exact_human_reviewed_evidence(self):
        r,p,s,report,ledger=prepared()
        item=extract_knowledge(r,p,s,ledger)
        self.assertEqual(item["knowledge_status"],"human_reviewed_claim")
        self.assertEqual(item["verdict"],"supported")
        self.assertEqual(len(item["evidence"]),4)
        self.assertEqual(item["scope"]["intervention"]["parameter"],"decode_tp")
        self.assertIn("limitations",item)

    def test_inconclusive_not_reusable(self):
        r,p,s,report,ledger=prepared("inconclusive")
        with self.assertRaisesRegex(ValueError,"Only Supported or Refuted"):
            extract_knowledge(r,p,s,ledger)

    def test_wrong_review_or_evidence_rejected(self):
        r,p,s,report,ledger=prepared()
        ledger["entries"][0]["review_sha256"]="0"*64
        from append_performance_review_decision import digest as unused
        payload={k:v for k,v in ledger["entries"][0].items() if k!="entry_sha256"}
        ledger["entries"][0]["entry_sha256"]=digest(payload)
        with self.assertRaisesRegex(ValueError,"different review packet"):
            extract_knowledge(r,p,s,ledger)

    def test_catalog_dedup_and_contradiction(self):
        r,p,s,report,ledger=prepared()
        item=extract_knowledge(r,p,s,ledger)
        catalog=build_catalog(item)
        with self.assertRaisesRegex(ValueError,"already exists"):
            build_catalog(item,catalog)
        opposite={**item,"knowledge_id":"pk-opposite","verdict":"refuted"}
        conflicted=build_catalog(opposite,catalog)
        self.assertEqual(len(conflicted["potential_contradictions"]),1)
        self.assertEqual(conflicted["potential_contradictions"][0]["resolution"],
                         "unresolved_human_review_required")

    def test_existing_contradictions_are_preserved(self):
        r,p,s,report,ledger=prepared()
        item=extract_knowledge(r,p,s,ledger)
        prior={"knowledge_id":"prior","topic":item["topic"],"scope_sha256":item["scope_sha256"],"verdict":"refuted"}
        old_conflict={"knowledge_id_a":"old-a","knowledge_id_b":"old-b","type":"existing","resolution":"unresolved_human_review_required"}
        catalog=build_catalog(item,{"schema_version":"1.0","entries":[prior],"potential_contradictions":[old_conflict]})
        self.assertIn(old_conflict,catalog["potential_contradictions"])
        self.assertEqual(len(catalog["potential_contradictions"]),2)

    def test_blocked_evidence_rejected(self):
        r,p,s,report,ledger=prepared()
        s["runs"][0].update(status="failed",reason="timeout")
        with self.assertRaises(ValueError):
            extract_knowledge(r,p,s,ledger)


if __name__=="__main__":
    unittest.main()
