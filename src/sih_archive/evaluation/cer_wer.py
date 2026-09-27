"""
Character Error Rate (CER) and Word Error Rate (WER) evaluation with operation breakdowns (Requirement R5).

Decomposes Levenshtein edit distance into substitutions (S), deletions (D), and insertions (I)
using rapidfuzz C++ SIMD-optimized alignment algorithms.
"""

import re
from typing import List, Tuple, Union
from rapidfuzz.distance import Levenshtein

from sih_archive.schemas.evaluation import EditOperationBreakdown


def normalize_text(
    text: str,
    remove_extra_whitespace: bool = True,
    strip_soft_hyphens: bool = True,
    case_sensitive: bool = True,
) -> str:
    """
    Normalizes text to prevent superficial whitespace or invisible character mismatches.

    Parameters:
        text: Raw input string.
        remove_extra_whitespace: Collapses contiguous whitespace characters to a single space.
        strip_soft_hyphens: Removes soft hyphens (\\u00ad) and zero-width spaces (\\u200b, \\ufeff).
        case_sensitive: If False, converts string to lowercase.

    Returns:
        Cleaned normalized string.
    """
    if text is None:
        return ""

    norm = text
    if strip_soft_hyphens:
        norm = norm.replace("\u00ad", "").replace("\u200b", "").replace("\ufeff", "")

    if remove_extra_whitespace:
        norm = re.sub(r"\s+", " ", norm).strip()

    if not case_sensitive:
        norm = norm.lower()

    return norm


def compute_cer(
    reference: str,
    hypothesis: str,
    normalize: bool = False,
    case_sensitive: bool = True,
) -> EditOperationBreakdown:
    """
    Computes Character Error Rate (CER) with explicit S, D, I decomposition.

    CER = (Substitutions + Deletions + Insertions) / Reference Length (N)

    Parameters:
        reference: Ground truth reference text.
        hypothesis: OCR hypothesis text.
        normalize: If True, applies whitespace normalization.
        case_sensitive: If False, evaluates case-insensitively.

    Returns:
        EditOperationBreakdown instance with counts and error_rate.
    """
    ref = normalize_text(reference, case_sensitive=case_sensitive) if normalize else (
        reference if case_sensitive else reference.lower()
    )
    hyp = normalize_text(hypothesis, case_sensitive=case_sensitive) if normalize else (
        hypothesis if case_sensitive else hypothesis.lower()
    )

    n_ref = len(ref)
    n_hyp = len(hyp)

    if n_ref == 0 and n_hyp == 0:
        return EditOperationBreakdown(
            substitutions=0,
            deletions=0,
            insertions=0,
            reference_length=0,
            hypothesis_length=0,
            total_distance=0,
            error_rate=0.0,
        )

    if n_ref == 0 and n_hyp > 0:
        return EditOperationBreakdown(
            substitutions=0,
            deletions=0,
            insertions=n_hyp,
            reference_length=0,
            hypothesis_length=n_hyp,
            total_distance=n_hyp,
            error_rate=1.0,
        )

    if n_ref > 0 and n_hyp == 0:
        return EditOperationBreakdown(
            substitutions=0,
            deletions=n_ref,
            insertions=0,
            reference_length=n_ref,
            hypothesis_length=0,
            total_distance=n_ref,
            error_rate=1.0,
        )

    ops = Levenshtein.editops(ref, hyp)
    substitutions = sum(1 for op in ops if op.tag == "replace")
    deletions = sum(1 for op in ops if op.tag == "delete")
    insertions = sum(1 for op in ops if op.tag == "insert")
    total_distance = substitutions + deletions + insertions
    error_rate = total_distance / float(n_ref)

    return EditOperationBreakdown(
        substitutions=substitutions,
        deletions=deletions,
        insertions=insertions,
        reference_length=n_ref,
        hypothesis_length=n_hyp,
        total_distance=total_distance,
        error_rate=float(error_rate),
    )


def compute_wer(
    reference: str,
    hypothesis: str,
    normalize: bool = False,
    case_sensitive: bool = True,
) -> EditOperationBreakdown:
    """
    Computes Word Error Rate (WER) with explicit S, D, I decomposition.

    WER = (Word Substitutions + Word Deletions + Word Insertions) / Reference Words (N)

    Parameters:
        reference: Ground truth reference text.
        hypothesis: OCR hypothesis text.
        normalize: If True, applies whitespace and control character normalization.
        case_sensitive: If False, evaluates case-insensitively.

    Returns:
        EditOperationBreakdown instance with counts and error_rate.
    """
    ref_norm = normalize_text(reference, case_sensitive=case_sensitive) if normalize else (
        reference if case_sensitive else reference.lower()
    )
    hyp_norm = normalize_text(hypothesis, case_sensitive=case_sensitive) if normalize else (
        hypothesis if case_sensitive else hypothesis.lower()
    )

    ref_words: List[str] = ref_norm.split()
    hyp_words: List[str] = hyp_norm.split()

    n_ref = len(ref_words)
    n_hyp = len(hyp_words)

    if n_ref == 0 and n_hyp == 0:
        return EditOperationBreakdown(
            substitutions=0,
            deletions=0,
            insertions=0,
            reference_length=0,
            hypothesis_length=0,
            total_distance=0,
            error_rate=0.0,
        )

    if n_ref == 0 and n_hyp > 0:
        return EditOperationBreakdown(
            substitutions=0,
            deletions=0,
            insertions=n_hyp,
            reference_length=0,
            hypothesis_length=n_hyp,
            total_distance=n_hyp,
            error_rate=1.0,
        )

    if n_ref > 0 and n_hyp == 0:
        return EditOperationBreakdown(
            substitutions=0,
            deletions=n_ref,
            insertions=0,
            reference_length=n_ref,
            hypothesis_length=0,
            total_distance=n_ref,
            error_rate=1.0,
        )

    ops = Levenshtein.editops(ref_words, hyp_words)
    substitutions = sum(1 for op in ops if op.tag == "replace")
    deletions = sum(1 for op in ops if op.tag == "delete")
    insertions = sum(1 for op in ops if op.tag == "insert")
    total_distance = substitutions + deletions + insertions
    error_rate = total_distance / float(n_ref)

    return EditOperationBreakdown(
        substitutions=substitutions,
        deletions=deletions,
        insertions=insertions,
        reference_length=n_ref,
        hypothesis_length=n_hyp,
        total_distance=total_distance,
        error_rate=float(error_rate),
    )
