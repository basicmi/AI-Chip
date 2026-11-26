import unittest
from test_performance_evidence_review import fixture
from review_performance_experiment_evidence import build_review,digest
from append_performance_review_decision import append_decision,validate_ledger,CHECKS


def inputs():
    r,p,s=fixture()
    report=build_review(r,p,s)
    d={"decision_id":"d1","reviewer":"fixture-reviewer","reviewed_at":"2026-11-26T00:00:00Z",
       "review_sha256":digest(report),"verdict":"supported","rationale":"Synthetic test only",
       "applicability":"Fixture context only","limitations":"Not production evidence",
       "supersedes":None,"checks":dict.fromkeys(CHECKS,True),
       "evidence_run_ids":[run["run_id"] for run in s["runs"]]}
    return {"schema_version":"1.0","entries":[]},r,p,s,d


class LedgerTests(unittest.TestCase):
    def test_append_and_revision(self):
        l,r,p,s,d=inputs()
        first=append_decision(l,r,p,s,d)
        self.assertEqual(len(l["entries"]),0)
        second=append_decision(first,r,p,s,{**d,"decision_id":"d2","supersedes":"d1","revision_reason":"Reassessment","verdict":"inconclusive"})
        self.assertEqual(second["entries"][0],first["entries"][0])
        self.assertEqual(len(second["entries"]),2)
        validate_ledger(second)

    def test_checks_and_citations(self):
        l,r,p,s,d=inputs()
        for patch in ({"checks":dict.fromkeys(CHECKS,False)},{"evidence_run_ids":["baseline0"]},{"evidence_run_ids":["unknown"]},{"review_sha256":"wrong"}):
            with self.assertRaises(ValueError):
                append_decision(l,r,p,s,{**d,**patch})

    def test_blocked_report(self):
        l,r,p,s,d=inputs()
        s["runs"][0].update(status="failed",reason="timeout")
        d["review_sha256"]=digest(build_review(r,p,s))
        with self.assertRaisesRegex(ValueError,"Blocked"):
            append_decision(l,r,p,s,d)
        self.assertEqual(len(append_decision(l,r,p,s,{**d,"verdict":"inconclusive"})["entries"]),1)

    def test_tamper_and_duplicate(self):
        l,r,p,s,d=inputs()
        first=append_decision(l,r,p,s,d)
        with self.assertRaises(ValueError):
            append_decision(first,r,p,s,{**d,"supersedes":"d1","revision_reason":"duplicate"})
        first["entries"][0]["decision"]["rationale"]="tampered"
        with self.assertRaisesRegex(ValueError,"digest"):
            validate_ledger(first)

    def test_revision_requires_reason(self):
        l,r,p,s,d=inputs()
        first=append_decision(l,r,p,s,d)
        with self.assertRaisesRegex(ValueError,"Revision reason"):
            append_decision(first,r,p,s,{**d,"decision_id":"d2","supersedes":"d1"})


if __name__=="__main__":
    unittest.main()
