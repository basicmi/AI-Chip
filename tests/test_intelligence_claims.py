import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from extract_intelligence_claims import (
    METHOD, extract_candidate_claims, extract_report, validate_claim, markdown_summary, relevance_for,
)


class ClaimExtractionTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {
            "candidate_id": "feed:nvidia:123",
            "candidate_type": "vendor_announcement",
            "source_id": "nvidia-news",
            "source_name": "NVIDIA Newsroom",
            "publisher": "NVIDIA",
            "source_type": "vendor_primary",
            "independence": "vendor",
            "url": "https://example.com/announcement",
            "published_at": "2026-11-12T00:00:00Z",
            "evidence_scope": "official_vendor_feed_metadata_and_excerpt",
            "title": "New AI GPU platform for LLM inference announced",
            "excerpt": (
                "The LLM inference system provides 72 GPUs per rack and up to 1.8 TB/s interconnect bandwidth. "
                "The platform supports FP8 inference."
            ),
        }

    def test_extracts_numeric_claims_and_scope(self):
        claims = extract_candidate_claims(self.candidate)
        numeric = [claim for claim in claims if claim["value"] is not None]
        self.assertEqual(len(numeric), 2)
        self.assertEqual(numeric[0]["value"], 72)
        self.assertEqual(numeric[0]["unit"].lower(), "gpus")
        self.assertEqual(numeric[0]["scope"]["status"], "explicit_per_unit")
        self.assertEqual(numeric[1]["value"], 1.8)
        self.assertEqual(numeric[1]["unit"].lower(), "tb/s")

    def test_qualitative_claim_has_no_invented_value(self):
        claims = extract_candidate_claims(self.candidate)
        qualitative = [claim for claim in claims if claim["value"] is None]
        self.assertTrue(any("supports FP8 inference" in claim["statement"] for claim in qualitative))
        self.assertTrue(all(claim["unit"] is None for claim in qualitative))

    def test_all_claims_remain_unverified_and_low_confidence(self):
        for claim in extract_candidate_claims(self.candidate):
            self.assertEqual(claim["review_status"], "unverified_candidate")
            self.assertEqual(claim["extraction"]["method"], METHOD)
            self.assertEqual(claim["extraction"]["confidence"], "low")
            self.assertEqual(validate_claim(claim), [])

    def test_rejects_invalid_source_url(self):
        self.assertEqual(
            extract_candidate_claims({**self.candidate, "url": "javascript:alert(1)"}), []
        )

    def test_preprint_is_labelled_as_preprint_not_verified(self):
        candidate = {
            **self.candidate,
            "candidate_type": "research_preprint",
            "source_type": "research_paper",
        }
        claims = extract_candidate_claims(candidate)
        self.assertTrue(claims)
        self.assertTrue(all(claim["review_status"] == "unverified_candidate" for claim in claims))
        self.assertTrue(all(claim["evidence_class"] == "research_preprint" for claim in claims))

    def test_research_performance_result_is_not_generic_research_finding(self):
        candidate = {
            **self.candidate,
            "candidate_type": "research_preprint",
            "source_type": "research_paper",
            "title": "GPU inference optimization",
            "excerpt": "Measured GPU inference latency falls by 18% in our evaluation.",
        }
        claim = extract_candidate_claims(candidate)[0]
        self.assertEqual(claim["claim_type"], "performance_result")
        self.assertEqual(claim["assertion_class"], "research_result_candidate")
        self.assertEqual(claim["evidence_class"], "research_preprint")

    def test_vendor_marketing_and_roadmap_are_distinguished(self):
        candidate = {
            **self.candidate,
            "excerpt": (
                "The GPU platform delivers the world's fastest inference performance. "
                "The vendor plans to support FP4 in Q2 2027."
            ),
        }
        claims = extract_candidate_claims(candidate)
        self.assertEqual(claims[0]["assertion_class"], "vendor_marketing_claim")
        self.assertEqual(claims[1]["assertion_class"], "roadmap_or_future_intent")

    def test_speculation_is_not_a_measured_result(self):
        candidate = {
            **self.candidate,
            "candidate_type": "research_preprint",
            "source_type": "research_paper",
            "title": "GPU architecture",
            "excerpt": "This architecture could enable higher throughput for GPU inference.",
        }
        claim = extract_candidate_claims(candidate)[0]
        self.assertEqual(claim["assertion_class"], "speculation_or_hypothesis")
        self.assertEqual(claim["claim_type"], "research_finding")

    def test_filters_unrelated_research_preprints(self):
        unrelated = [
            {
                **self.candidate,
                "candidate_type": "research_preprint",
                "source_type": "research_paper",
                "title": "Internalizing Investment Mandates: A Neurosymbolic RL Approach",
                "excerpt": (
                    "Deep reinforcement learning improves financial performance. "
                    "The policy reduces violations from 33.4% to 4.8% at inference time."
                ),
            },
            {
                **self.candidate,
                "candidate_type": "research_preprint",
                "source_type": "research_paper",
                "title": "FLEX-LBP: Texture Classification",
                "excerpt": (
                    "The descriptor improves nearest-neighbor accuracy by 3.55 points. "
                    "The code is available as a drop-in PyTorch layer."
                ),
                "url": "https://arxiv.org/abs/2611.00001",
            },
        ]
        for candidate in unrelated:
            self.assertEqual(extract_candidate_claims(candidate), [])

    def test_token_boundaries_prevent_false_eda_match_inside_url(self):
        candidate = {
            **self.candidate,
            "title": "Medical image descriptor",
            "excerpt": (
                "The code is available at https://github.com/medalimoussa/FLEX-LBP "
                "and improves accuracy by 3.5%."
            ),
        }
        self.assertEqual(extract_candidate_claims(candidate), [])

    def test_title_is_context_not_an_asserted_claim(self):
        candidate = {
            **self.candidate,
            "title": "GPU X: A New Accelerator Architecture",
            "excerpt": "The platform provides 80 GB HBM per GPU.",
        }
        claims = extract_candidate_claims(candidate)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["statement"], "The platform provides 80 GB HBM per GPU.")
        self.assertNotIn("GPU X:", claims[0]["statement"])

    def test_report_and_summary_include_quality_distributions(self):
        report = extract_report(
            {"review_queue": [self.candidate]},
            generated_at="2026-11-13T00:00:00Z",
        )
        self.assertEqual(report["claim_count"], len(report["claims"]))
        self.assertIn("direct_ai_compute", report["relevance_counts"])
        self.assertIn("vendor_primary_statement", report["evidence_class_counts"])
        self.assertIn("technical_specification_candidate", report["assertion_class_counts"])
        self.assertIn("human review required", markdown_summary(report))
        self.assertIn("routing labels", report["policy"])

    def test_deduplicates_identical_sentence(self):
        candidate = {
            **self.candidate,
            "title": "Overview of LLM inference GPU platform",
            "excerpt": (
                "The system provides 72 GPUs per rack. "
                "The system provides 72 GPUs per rack."
            ),
        }
        self.assertEqual(len(extract_candidate_claims(candidate)), 1)

    def test_round_robin_limit_preserves_multiple_sources(self):
        def candidate(cid, source_id, title, excerpt):
            return {
                **self.candidate,
                "candidate_id": cid,
                "source_id": source_id,
                "title": title,
                "excerpt": excerpt,
            }
        discovery = {
            "review_queue": [
                candidate("a1", "source-a", "GPU inference platform",
                          "GPU inference throughput improves by 12%. GPU inference latency falls by 8 ms."),
                candidate("a2", "source-a", "GPU serving platform",
                          "GPU serving throughput improves by 20%. GPU serving latency falls by 4 ms."),
                candidate("b1", "source-b", "HBM memory system",
                          "HBM bandwidth reaches 3 TB/s. HBM capacity reaches 96 GB."),
            ]
        }
        report = extract_report(discovery, max_claims=2, max_claims_per_candidate=10)
        self.assertEqual(report["claim_count"], 2)
        self.assertEqual(
            {claim["source"]["source_id"] for claim in report["claims"]},
            {"source-a", "source-b"},
        )
        self.assertTrue(report["truncated"])
        self.assertEqual(report["claims_dropped_by_limits"], 4)

    def test_report_rejects_invalid_limits_and_discovery_shape(self):
        with self.assertRaisesRegex(ValueError, "max_claims"):
            extract_report({"review_queue": []}, max_claims=0)
        with self.assertRaisesRegex(ValueError, "max_claims_per_candidate"):
            extract_report({"review_queue": []}, max_claims_per_candidate=0)
        with self.assertRaisesRegex(ValueError, "review_queue"):
            extract_report({"candidates": []})

    def test_validation_rejects_unknown_assertion_class(self):
        claim = extract_candidate_claims(self.candidate)[0]
        claim["assertion_class"] = "verified_fact"
        self.assertIn("invalid assertion class", validate_claim(claim))

    def test_schema_contract_matches_extractor_v3(self):
        schema = json.loads((ROOT / "schemas/intelligence-claims.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["extraction_method"]["const"], METHOD)
        claim = schema["$defs"]["claim"]
        for field in ("assertion_class", "relevance", "evidence_class"):
            self.assertIn(field, claim["required"])
            self.assertIn(field, claim["properties"])
        self.assertEqual(claim["properties"]["extraction"]["properties"]["method"]["const"], METHOD)
        self.assertEqual(claim["properties"]["extraction"]["properties"]["confidence"]["const"], "low")

    def test_filters_generic_gpu_hpc_and_unrelated_world_models(self):
        unrelated = [
            ("Multi-GPU Tridiagonal Partition Algorithm",
             "A multi-GPU recursive parallel partition method for tridiagonal linear algebra implemented in CUDA."),
            ("WeatherDreamer: Learning a World Model from Earth Observations",
             "We introduce a world model for global weather forecasting using observations from satellites."),
            ("GEAR: GPU-Accelerated Global Solver",
             "A GPU-accelerated solver for nonlinear programs and neural-network verification."),
            ("Numerical Bugs in GPU Programs",
             "General-purpose GPU computing supports scientific computing and deep learning libraries."),
            ("Decision Transformer for Offline Meta-Reinforcement Learning",
             "A generic offline meta-RL method learns latent task representations for policy generation."),
        ]
        for title, excerpt in unrelated:
            with self.subTest(title=title):
                self.assertIsNone(relevance_for(title + " " + excerpt)[0])

    def test_keeps_specific_ai_hardware_system_and_physical_ai_signals(self):
        cases = [
            ("OverlapAdvisor: Distributed MoE Serving",
             "MoE inference with expert parallelism relies on All-to-All communication."),
            ("Firepool: Warm GPU Capacity for Agentic and RL Workloads",
             "AI agents and RL trainers run isolated GPU jobs; the execution broker keeps GPU pods warm."),
            ("On-Device Reinforcement Learning Runtime",
             "On-device reinforcement learning runs an actor and learner on one embedded GPU."),
            ("Vision-Language-Action Models",
             "VLA models output robot actions for physical control."),
            ("EmbodiedIntentBench",
             "Mobile robotic sensing systems need runtime adaptation under resource constraints."),
        ]
        expected = [
            "direct_ai_compute", "direct_ai_compute", "direct_ai_compute",
            "adjacent_ai_systems", "adjacent_ai_systems",
        ]
        for (title, excerpt), label in zip(cases, expected):
            with self.subTest(title=title):
                self.assertEqual(relevance_for(title + " " + excerpt)[0], label)

    def test_per_candidate_limit_is_reported(self):
        candidate = {
            **self.candidate,
            "title": "GPU inference system",
            "excerpt": (
                "GPU inference throughput improves by 12%. "
                "GPU inference latency falls by 8 ms. "
                "GPU memory capacity reaches 96 GB."
            ),
        }
        report = extract_report(
            {"review_queue": [candidate]},
            max_claims=100,
            max_claims_per_candidate=1,
        )
        self.assertEqual(report["claim_count"], 1)
        self.assertGreaterEqual(report["claim_count_before_limits"], 3)
        self.assertGreaterEqual(report["claims_dropped_by_limits"], 2)
        self.assertTrue(report["truncated"])


if __name__ == "__main__":
    unittest.main()
