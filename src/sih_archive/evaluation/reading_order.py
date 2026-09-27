"""
Reading order evaluation baseline abstraction and Kendall's Tau sequence alignment (Requirement R5).

RESEARCH BASELINE NOTICE:
Evaluating historical manuscript reading order using 1D sequence alignment and Kendall's
rank correlation coefficient (Kendall's Tau) represents a foundational baseline.
Complex historical layouts (multi-column broadsheets, marginalia, footnotes, interlinear glosses)
often exhibit non-linear 2D topological reading paths. This module provides an extensible
abstraction layer for research evaluation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Tuple


class ReadingOrderEvaluator(ABC):
    """
    Abstract baseline interface for reading order evaluation algorithms.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Evaluator identifier."""
        pass

    @abstractmethod
    def evaluate(
        self,
        matched_pairs: Sequence[Tuple[int, int, ...]],
        total_hyp_regions: Optional[int] = None,
        total_ref_regions: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Computes reading order consistency metrics over matched region pairs.

        Parameters:
            matched_pairs: Sequence of tuples where element 0 is hypothesis index
                           and element 1 is reference index (e.g. (hyp_idx, ref_idx, ...)).
            total_hyp_regions: Total regions detected in hypothesis.
            total_ref_regions: Total regions in ground truth reference.

        Returns:
            Dictionary containing 'score' (in [0.0, 1.0]), 'kendall_tau',
            inversion statistics, and research metadata.
        """
        pass


class KendallTauReadingOrderEvaluator(ReadingOrderEvaluator):
    """
    Evaluates reading order consistency using Kendall's Tau rank correlation and
    normalized inversion distance on IoU-matched region pairs.
    """

    @property
    def name(self) -> str:
        return "kendall_tau_baseline"

    def evaluate(
        self,
        matched_pairs: Sequence[Tuple[int, int, ...]],
        total_hyp_regions: Optional[int] = None,
        total_ref_regions: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculates Kendall's Tau rank correlation coefficient between reference and hypothesis order.
        """
        k = len(matched_pairs)
        if k == 0:
            return {
                "name": self.name,
                "score": 1.0,
                "kendall_tau": 1.0,
                "normalized_inversion_distance": 0.0,
                "concordant_pairs": 0,
                "discordant_pairs": 0,
                "total_pairs": 0,
                "matched_count": 0,
                "baseline_type": "evolving_research_baseline",
            }

        if k == 1:
            return {
                "name": self.name,
                "score": 1.0,
                "kendall_tau": 1.0,
                "normalized_inversion_distance": 0.0,
                "concordant_pairs": 0,
                "discordant_pairs": 0,
                "total_pairs": 0,
                "matched_count": 1,
                "baseline_type": "evolving_research_baseline",
            }

        # Order pairs according to reference index
        sorted_by_ref = sorted(matched_pairs, key=lambda pair: pair[1])
        hyp_order = [pair[0] for pair in sorted_by_ref]

        concordant = 0
        discordant = 0
        ties = 0
        total_possible_pairs = (k * (k - 1)) // 2

        for i in range(k):
            for j in range(i + 1, k):
                if hyp_order[i] < hyp_order[j]:
                    concordant += 1
                elif hyp_order[i] > hyp_order[j]:
                    discordant += 1
                else:
                    ties += 1

        denom = total_possible_pairs
        tau = (concordant - discordant) / float(denom) if denom > 0 else 1.0
        norm_inv_dist = discordant / float(denom) if denom > 0 else 0.0

        # Map tau [-1.0, 1.0] to normalized score [0.0, 1.0]
        normalized_score = max(0.0, min(1.0, (tau + 1.0) / 2.0))

        return {
            "name": self.name,
            "score": round(normalized_score, 4),
            "kendall_tau": round(tau, 4),
            "normalized_inversion_distance": round(norm_inv_dist, 4),
            "concordant_pairs": concordant,
            "discordant_pairs": discordant,
            "ties": ties,
            "total_pairs": total_possible_pairs,
            "matched_count": k,
            "baseline_type": "evolving_research_baseline",
        }
