"""Unit tests for Character Error Rate (CER) and Word Error Rate (WER) metrics (Requirement R5)."""

import pytest
from sih_archive.evaluation.cer_wer import compute_cer, compute_wer, normalize_text
from sih_archive.schemas.evaluation import EditOperationBreakdown


def test_normalize_text_whitespace_and_hyphens():
    """Verify normalize_text collapses whitespace and strips soft hyphens."""
    raw = "Dr.   Babasaheb\t\tAmbedkar \n\n Writings\u00ad and\u200b Speeches"
    cleaned = normalize_text(raw)
    assert cleaned == "Dr. Babasaheb Ambedkar Writings and Speeches"


def test_normalize_text_case_sensitivity():
    """Verify normalize_text lowercases text when case_sensitive=False."""
    raw = "Constituent Assembly of India"
    assert normalize_text(raw, case_sensitive=True) == "Constituent Assembly of India"
    assert normalize_text(raw, case_sensitive=False) == "constituent assembly of india"


def test_cer_identical_strings():
    """Verify CER for identical strings is exactly 0.0 with 0 edit operations."""
    text = "Educate Agitate Organise"
    res = compute_cer(text, text)
    assert res.error_rate == 0.0
    assert res.substitutions == 0
    assert res.deletions == 0
    assert res.insertions == 0
    assert res.total_distance == 0
    assert res.reference_length == len(text)
    assert res.hypothesis_length == len(text)


def test_cer_pure_substitution():
    """Verify CER correctly tracks substitution operations."""
    # 'cat' -> 'bat' (1 substitution, length 3)
    res = compute_cer("cat", "bat")
    assert res.substitutions == 1
    assert res.deletions == 0
    assert res.insertions == 0
    assert res.total_distance == 1
    assert res.reference_length == 3
    assert res.error_rate == pytest.approx(1.0 / 3.0)


def test_cer_pure_deletion():
    """Verify CER correctly tracks deletion operations."""
    # 'cats' -> 'cat' (1 deletion from reference)
    res = compute_cer("cats", "cat")
    assert res.substitutions == 0
    assert res.deletions == 1
    assert res.insertions == 0
    assert res.total_distance == 1
    assert res.reference_length == 4
    assert res.error_rate == 0.25


def test_cer_pure_insertion():
    """Verify CER correctly tracks insertion operations."""
    # 'cat' -> 'cats' (1 insertion in hypothesis)
    res = compute_cer("cat", "cats")
    assert res.substitutions == 0
    assert res.deletions == 0
    assert res.insertions == 1
    assert res.total_distance == 1
    assert res.reference_length == 3
    assert res.error_rate == pytest.approx(1.0 / 3.0)


def test_cer_empty_edge_cases():
    """Verify CER edge case handling for empty strings."""
    # Both empty
    both_empty = compute_cer("", "")
    assert both_empty.error_rate == 0.0
    assert both_empty.total_distance == 0

    # Reference empty, hypothesis non-empty
    ref_empty = compute_cer("", "Ambedkar")
    assert ref_empty.error_rate == 1.0
    assert ref_empty.insertions == len("Ambedkar")
    assert ref_empty.deletions == 0
    assert ref_empty.reference_length == 0
    assert ref_empty.hypothesis_length == len("Ambedkar")

    # Reference non-empty, hypothesis empty
    hyp_empty = compute_cer("Ambedkar", "")
    assert hyp_empty.error_rate == 1.0
    assert hyp_empty.deletions == len("Ambedkar")
    assert hyp_empty.insertions == 0
    assert hyp_empty.reference_length == len("Ambedkar")


def test_cer_unbounded_insertion_exceeding_one():
    """Verify CER can legitimately exceed 1.0 when severe OCR hallucination inserts excessive text."""
    ref = "Drafting Committee"
    # Hypothesis is 4 times longer than reference
    hyp = "Drafting Committee Drafting Committee Drafting Committee Drafting Committee"
    res = compute_cer(ref, hyp)
    assert res.error_rate > 1.0
    assert res.insertions > 0


def test_cer_unicode_and_marathi_scripts():
    """Verify CER calculates accurately on Indic/Devanagari scripts."""
    ref = "डॉ. बाबासाहेब आंबेडकर"
    hyp = "डा. बाबासाहेब आंबेडकर"  # First word has 1 character substitution
    res = compute_cer(ref, hyp)
    assert res.substitutions == 1
    assert res.error_rate > 0.0
    assert res.error_rate < 0.2


def test_wer_identical_words():
    """Verify WER is 0.0 for identical word sequences."""
    text = "Dr. Babasaheb Ambedkar Writings and Speeches"
    res = compute_wer(text, text)
    assert res.error_rate == 0.0
    assert res.substitutions == 0
    assert res.deletions == 0
    assert res.insertions == 0
    assert res.reference_length == 6
    assert res.hypothesis_length == 6


def test_wer_substitutions_and_deletions():
    """Verify WER accurately decomposes word edits into S, D, and I."""
    ref = "The Constitution of India was adopted"
    # Delete 'The' (D), change 'India' -> 'Bharat' (S), insert 'duly' (I)
    hyp = "Constitution of Bharat was duly adopted"
    res = compute_wer(ref, hyp)
    assert res.substitutions == 1
    assert res.deletions == 1
    assert res.insertions == 1
    assert res.total_distance == 3
    assert res.reference_length == 6
    assert res.hypothesis_length == 6
    assert res.error_rate == pytest.approx(3.0 / 6.0)


def test_wer_empty_edge_cases():
    """Verify WER behaves consistently with empty references and hypotheses."""
    assert compute_wer("", "").error_rate == 0.0
    assert compute_wer("", "word").error_rate == 1.0
    assert compute_wer("word", "").error_rate == 1.0


def test_cer_wer_normalization_flags():
    """Verify that normalize=True and case_sensitive=False mitigate formatting noise."""
    ref = "Volume 1: Speeches"
    hyp = "volume  1:   speeches"

    # Verbatim CER has mismatches due to case and whitespace
    raw_cer = compute_cer(ref, hyp, normalize=False, case_sensitive=True)
    assert raw_cer.error_rate > 0.0

    # Normalized CER evaluates cleanly
    norm_cer = compute_cer(ref, hyp, normalize=True, case_sensitive=False)
    assert norm_cer.error_rate == 0.0

    # Same for WER
    norm_wer = compute_wer(ref, hyp, normalize=True, case_sensitive=False)
    assert norm_wer.error_rate == 0.0
