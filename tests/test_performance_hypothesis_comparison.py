import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_performance_hypotheses import compare


def diagnosis(candidates):
    return {"schema_version":"1.0","record_id":"fixture-record",
            "overall_verdict":"undetermined",
            "attribution":{"verdict":"undetermined","candidates":candidates}}


def catalog():
    return {"schema_version":"1.0","hypotheses":[
        {"hypothesis_id":"comm","title":"Communication","mechanism":"communication",
         "statement":"Communication may be on critical path.","knowledge_query":"all to all communication",
         "evidence_rules":[{"mechanism":"communication_link_utilization","interpretation":"Link activity is not critical-path proof."}],
         "discriminating_measurements":["Collective timing"],"what_would_support":["Collective critical path changes"],"what_would_weaken":["No critical path change"]},
        {"hypothesis_id":"runtime","title":"Runtime","mechanism":"runtime",
         "statement":"Queueing may contribute.","knowledge_query":"queueing scheduler",
         "evidence_rules":[{"mechanism":"runtime_scheduling_or_queueing","interpretation":"Serving metrics do not isolate queueing."}],
         "discriminating_measurements":["Queue trace"],"what_would_support":["Queue wait changes"],"what_would_weaken":["No queue wait"]}]}


class HypothesisComparisonTests(unittest.TestCase):
    def test_observed_signal_is_not_causal_verdict(self):
        d=diagnosis([{"mechanism":"communication_link_utilization","status":"observed",
            "observation":"Link utilization 80%.","evidence":["tx","rx"],
            "not_proven":"Does not prove critical-path contention."}])
        result=compare(d,catalog())
        self.assertEqual(result["hypotheses"][0]["evidence_state"],"supporting_signal_observed")
        self.assertEqual(result["overall_verdict"],"undetermined")
        self.assertEqual(result["ranking"],"none")
        self.assertIn("not_proven",result["hypotheses"][0]["observations"][0])

    def test_not_observed_only_applies_to_sampled_window(self):
        d=diagnosis([{"mechanism":"runtime_scheduling_or_queueing","status":"not_observed_in_window",
            "observation":"No throttle event."}])
        result=compare(d,catalog())
        runtime=next(x for x in result["hypotheses"] if x["hypothesis_id"]=="runtime")
        self.assertEqual(runtime["evidence_state"],"not_observed_in_sampled_window")
        self.assertIn("does not exclude",runtime["interpretation"])

    def test_missing_diagnostic_channel_is_not_negative_evidence(self):
        result=compare(diagnosis([]),catalog())
        self.assertEqual(result["hypotheses"][0]["evidence_state"],"no_direct_diagnostic_evidence")
        self.assertTrue(result["hypotheses"][0]["missing_diagnostic_channels"])

    def test_historical_knowledge_is_reference_not_vote(self):
        retrieval={"report_type":"performance_knowledge_retrieval","results":[{
            "knowledge_id":"pk-1","topic":"communication","reviewer_interpretation":"All-to-all traffic increased.",
            "applicability":"Only the declared topology.","limitations":"One configuration.",
            "verdict":"supported","retrieval_tier":"exploratory_only",
            "applicability_status":"insufficient_context","metric_compatibility":"not_assessed",
            "evidence_refs":[{"run_id":"r1"}]}]}
        result=compare(diagnosis([]),catalog(),retrieval)
        comm=result["hypotheses"][0]
        self.assertEqual(comm["historical_knowledge"][0]["knowledge_id"],"pk-1")
        self.assertEqual(comm["evidence_state"],"no_direct_diagnostic_evidence")

    def test_invalid_diagnosis_and_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            compare({"schema_version":"1.0","overall_verdict":"supported","attribution":{"candidates":[]}},catalog())
        bad={"schema_version":"1.0","hypotheses":[catalog()["hypotheses"][0],catalog()["hypotheses"][0]]}
        with self.assertRaises(ValueError):
            compare(diagnosis([]),bad)

    def test_invalid_candidate_state_rejected(self):
        with self.assertRaises(ValueError):
            compare(diagnosis([{"mechanism":"x","status":"proven"}]),catalog())


if __name__=="__main__":
    unittest.main()
