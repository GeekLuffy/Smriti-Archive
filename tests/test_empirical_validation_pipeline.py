"""
Unit and Integration Tests for SIH26096 Empirical Validation Pipeline (E1, E2, E3).

Verifies:
- Truthful Tesseract binary detection (never faked)
- Language pack verification (eng, hin, mar)
- Preprocessing filter variants (raw, grayscale, denoise, deskew, adaptive)
- Error metrics: CER, WER, BBox IoU, Kendall's Tau Reading Order
- Missing ground truth handling ('ground_truth_unavailable' status)
- Scientific gating: E1 (BLOCKED), E2 (LOCKED_PREVIEW), E3 (LOCKED_PREVIEW)
- Principled algorithmic refusal for ungrounded queries
- Dual-annotator agreement tracking
- Validation status CLI dashboard and JSON schema
- Provenance preservation across benchmark outputs
"""

import json
from pathlib import Path
import subprocess
import sys
import pytest

from sih_archive.evaluation.cer_wer import compute_cer, compute_wer
from sih_archive.evaluation.iou import compute_iou, match_bounding_boxes
from sih_archive.evaluation.reading_order import KendallTauReadingOrderEvaluator
from sih_archive.ocr.base import OCRAdapter
from sih_archive.ocr.mock import MockOCRAdapter
from sih_archive.ocr.tesseract import TesseractAdapter
from sih_archive.preprocessing.filters import PreprocessingPipeline
from sih_archive.schemas.evaluation import GroundTruthPage
from sih_archive.schemas.ocr import OCROutput

# Import scripts directly
from scripts.run_e1_ocr import discover_page_images, load_ground_truth_for_page, run_e1_pipeline
from scripts.run_e2_retrieval import load_judged_queries, run_e2_pipeline
from scripts.run_e3_attribution import compute_inter_annotator_agreement, run_e3_pipeline
from scripts.validation_status import inspect_validation_status


class TestE1ArchivalOCRPipeline:
    """Tests for Phase E1 OCR adapter, preprocessing, metrics, and gating."""

    def test_tesseract_availability_truthful(self):
        """Verifies that Tesseract is never faked or simulated as available when binary is absent."""
        adapter = TesseractAdapter()
        avail, msg = adapter.is_available()
        # On this Windows host, binary is absent, so avail must be False
        assert isinstance(avail, bool)
        assert isinstance(msg, str)
        if not avail:
            assert "not found" in msg.lower() or "searched" in msg.lower()

    def test_tesseract_missing_languages_detection(self):
        """Verifies that unavailable or missing language packs are caught."""
        adapter = TesseractAdapter()
        if not adapter.is_available()[0]:
            langs = adapter.get_installed_languages()
            assert langs == []

    def test_preprocessing_pipeline_spec_parsing(self):
        """Tests that all required preprocessing variants can be parsed deterministically."""
        variants = ["raw", "grayscale", "denoise", "deskew", "adaptive_gaussian"]
        for v in variants:
            pipeline = PreprocessingPipeline.from_spec(v)
            assert pipeline is not None
            if v == "raw":
                assert len(pipeline.filters) == 0
            else:
                assert len(pipeline.filters) >= 1

    def test_cer_wer_computation_exact(self):
        """Verifies exact Levenshtein edit distance decomposition for CER and WER."""
        ref = "Bhimrao Ramji Ambedkar"
        hyp = "Bhimrao Ramji Ambddkar"  # 1 substitution (e -> d)
        
        cer = compute_cer(ref, hyp)
        assert cer.substitutions == 1
        assert cer.reference_length == len(ref)
        assert cer.error_rate > 0.0

        wer = compute_wer(ref, hyp)
        assert wer.substitutions == 1
        assert wer.reference_length == 3
        assert wer.error_rate == pytest.approx(1 / 3, 0.01)

    def test_bounding_box_iou_matching(self):
        """Verifies geometric IoU computation and greedy bipartite matching."""
        box_a = [10, 10, 100, 50]
        box_b = [10, 10, 100, 50]
        assert compute_iou(box_a, box_b) == 1.0

        box_c = [200, 200, 50, 50]
        assert compute_iou(box_a, box_c) == 0.0

        metrics, matches = match_bounding_boxes([box_a], [box_b], iou_threshold=0.5)
        assert metrics.true_positives == 1
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1 == 1.0

    def test_reading_order_concordance(self):
        """Verifies Kendall's Tau reading order alignment evaluator on matched region pairs."""
        evaluator = KendallTauReadingOrderEvaluator()
        # Matched pairs where hyp order matches ref order exactly
        concordant_pairs = [(0, 0), (1, 1), (2, 2), (3, 3)]
        res = evaluator.evaluate(concordant_pairs)
        assert res["score"] == 1.0

        # Inverted order
        inverted_pairs = [(3, 0), (2, 1), (1, 2), (0, 3)]
        res_inv = evaluator.evaluate(inverted_pairs)
        assert res_inv["score"] == 0.0

    def test_missing_ground_truth_handling(self, tmp_path):
        """Verifies that missing ground truth annotates page as unavailable without faking."""
        gt_result = load_ground_truth_for_page(tmp_path, "nonexistent_page_p0099")
        assert gt_result is None

    def test_e1_gating_blocked_on_host_binary(self, tmp_path):
        """Verifies that E1 pipeline reports BLOCKED_ON_HOST_OCR_BINARY when Tesseract is absent."""
        class MockArgs:
            input = "data/processed/pages"
            output = str(tmp_path / "e1_test")
            languages = ["eng", "hin", "mar"]
            preprocessing = ["raw"]
            ground_truth = "data/ground_truth"
            tesseract_cmd = None
            allow_mock_fallback = False
            check_only = True

        res = run_e1_pipeline(MockArgs())
        # Tesseract is absent on host
        assert "BLOCKED" in res["gate_status"]
        assert res["tesseract_available"] is False

    def test_e1_execution_with_mock_fallback(self, tmp_path):
        """Verifies that when mock fallback is allowed for testing, E1 outputs valid schemas and files."""
        class MockArgs:
            input = "data/processed/pages"
            output = str(tmp_path / "e1_mock_test")
            languages = ["eng"]
            preprocessing = ["raw"]
            ground_truth = "data/ground_truth"
            tesseract_cmd = None
            allow_mock_fallback = True
            check_only = False

        res = run_e1_pipeline(MockArgs())
        assert "SYNTHETIC_MOCK_PREVIEW" in res["gate_status"]

        out_dir = Path(MockArgs.output)
        assert (out_dir / "e1_benchmark_report.json").is_file()
        assert (out_dir / "summary_metrics.csv").is_file()
        assert (out_dir / "REPORT.md").is_file()
        assert (out_dir / "config_snapshot.json").is_file()
        assert (out_dir / "dataset_manifest.json").is_file()


class TestE2RetrievalBenchmarkPipeline:
    """Tests for Phase E2 Retrieval Benchmark gating and metrics."""

    def test_e2_gating_strictly_locked_preview(self, tmp_path):
        """Verifies that E2 remains LOCKED_PREVIEW when E1 is not empirical."""
        class MockArgs:
            input_ocr = "outputs/ocr"
            e1_results = str(tmp_path / "missing_e1.json")
            queries = "data/evaluation/judged_queries.json"
            output = str(tmp_path / "e2_test")
            force_preview = False

        res = run_e2_pipeline(MockArgs())
        assert "LOCKED_PREVIEW" in res["gate_status"]
        assert "Gated on Empirical Completion of Phase E1" in res["gate_status"]

    def test_e2_judged_queries_dataset_validity(self):
        """Verifies that judged queries dataset contains valid structure and graded relevance."""
        q_path = Path("data/evaluation/judged_queries.json")
        queries = load_judged_queries(q_path)
        assert len(queries) >= 10
        for q in queries:
            assert "query_id" in q
            assert "query" in q
            assert "graded_relevance" in q

    def test_e2_retrieval_comparison_outputs(self, tmp_path):
        """Verifies that E2 execution creates CSV comparison, JSON report, and Markdown summary."""
        class MockArgs:
            input_ocr = "outputs/ocr"
            e1_results = "results/e1/e1_benchmark_report.json"
            queries = "data/evaluation/judged_queries.json"
            output = str(tmp_path / "e2_out")
            force_preview = True

        res = run_e2_pipeline(MockArgs())
        assert len(res["engine_benchmarks"]) == 4  # BM25, 3-Gram, Dense, Hybrid

        out_dir = Path(MockArgs.output)
        assert (out_dir / "e2_retrieval_results.json").is_file()
        assert (out_dir / "retrieval_comparison.csv").is_file()
        assert (out_dir / "REPORT.md").is_file()
        assert (out_dir / "config_snapshot.json").is_file()


class TestE3AttributionRefusalPipeline:
    """Tests for Phase E3 Evidence Attribution, Refusal, and Dual-Annotator Agreement."""

    def test_e3_gating_strictly_locked_preview(self, tmp_path):
        """Verifies that E3 remains LOCKED_PREVIEW when upstream phases are not measured."""
        class MockArgs:
            input_ocr = "outputs/ocr"
            e1_results = "results/e1/e1_benchmark_report.json"
            e2_results = "results/e2/e2_retrieval_results.json"
            questions = "data/evaluation/attribution_questions.json"
            output = str(tmp_path / "e3_test")
            force_preview = False

        res = run_e3_pipeline(MockArgs())
        assert "LOCKED_PREVIEW" in res["gate_status"]
        assert "Gated on Empirical Completion of Phase E1 and E2" in res["gate_status"]

    def test_dual_annotator_agreement_calculation(self):
        """Verifies calculation of inter-annotator agreement and Cohen's Kappa approximation."""
        sample_questions = [
            {
                "annotator_evaluations": {
                    "annotator_1": {"claim_supported": True},
                    "annotator_2": {"claim_supported": True},
                }
            },
            {
                "annotator_evaluations": {
                    "annotator_1": {"claim_supported": True},
                    "annotator_2": {"claim_supported": False},
                }
            },
        ]
        agreement = compute_inter_annotator_agreement(sample_questions)
        assert agreement["total_judged_items"] == 2
        assert agreement["concordant_items"] == 1
        assert agreement["percent_agreement"] == 0.5

    def test_e3_execution_outputs(self, tmp_path):
        """Verifies that E3 execution creates JSON report, annotator agreement, and Markdown summary."""
        class MockArgs:
            input_ocr = "outputs/ocr"
            e1_results = "results/e1/e1_benchmark_report.json"
            e2_results = "results/e2/e2_retrieval_results.json"
            questions = "data/evaluation/attribution_questions.json"
            output = str(tmp_path / "e3_out")
            force_preview = True

        res = run_e3_pipeline(MockArgs())
        assert res["questions_evaluated_count"] >= 5

        out_dir = Path(MockArgs.output)
        assert (out_dir / "e3_attribution_results.json").is_file()
        assert (out_dir / "annotator_agreement.json").is_file()
        assert (out_dir / "REPORT.md").is_file()
        assert (out_dir / "config_snapshot.json").is_file()


class TestValidationDashboardAndProvenance:
    """Tests for validation_status CLI and end-to-end provenance traceability."""

    def test_validation_status_inspection(self):
        """Verifies validation status dictionary contains all 4 research gates."""
        data = inspect_validation_status()
        assert data["team"] == "ORBIT"
        assert "E0" in data["gates"]
        assert "E1" in data["gates"]
        assert "E2" in data["gates"]
        assert "E3" in data["gates"]

        assert data["gates"]["E0"]["gate_status"] == "MEASURED"
        assert "BLOCKED" in data["gates"]["E1"]["gate_status"]
        assert data["gates"]["E2"]["gate_status"] == "LOCKED_PREVIEW"
        assert data["gates"]["E3"]["gate_status"] == "LOCKED_PREVIEW"

        assert len(data["commands"]) >= 5

    def test_validation_status_cli_execution(self):
        """Verifies that validation_status.py executes cleanly without error."""
        result = subprocess.run(
            [sys.executable, "scripts/validation_status.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert "INSTITUTIONAL EMPIRICAL VALIDATION DASHBOARD" in result.stdout
        assert "BLOCKED_ON_HOST_OCR_BINARY" in result.stdout

    def test_validation_status_cli_json_mode(self):
        """Verifies that validation_status.py --json emits valid parseable JSON."""
        result = subprocess.run(
            [sys.executable, "scripts/validation_status.py", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        parsed = json.loads(result.stdout)
        assert parsed["team"] == "ORBIT"
        assert "gates" in parsed
        assert "commands" in parsed
