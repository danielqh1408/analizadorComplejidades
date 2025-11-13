"""
Comparison Module

This module compares the complexity results from:
1. The deterministic analyzer.
2. The LLM validation step.

Its purpose is to provide a structured comparison result
to identify agreement, discrepancy, and confidence levels.
"""

from typing import Dict, Any


class ComplexityComparator:
    """
    Handles comparison logic between deterministic and LLM results.
    """

    def __init__(self):
        self.keys_to_compare = ["O", "Omega", "Theta"]

    def normalize_notation(self, value: str) -> str:
        """
        Normalizes complexity notation to a canonical lowercase format.
        Example: "O(N^2)" → "o(n^2)"
        """
        if not value:
            return "n/a"
        return value.strip().lower().replace(" ", "")

    def compare_results(
        self,
        deterministic: Dict[str, Any],
        llm_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compare both sources and return a structured comparison.
        """
        comparison = {}
        match_count = 0

        for key in self.keys_to_compare:
            det_value = self.normalize_notation(deterministic.get(key, "n/a"))
            llm_value = self.normalize_notation(llm_result.get(key, "n/a"))
            match = det_value == llm_value

            comparison[key] = {
                "deterministic": det_value,
                "llm": llm_value,
                "match": match,
            }

            if match:
                match_count += 1

        total = len(self.keys_to_compare)
        agreement_score = round((match_count / total) * 100, 2)

        # Build final summary
        summary = {
            "agreement_score": agreement_score,
            "all_match": agreement_score == 100.0,
            "details": comparison,
            "llm_explanation": llm_result.get("explanation", "No explanation provided.")
        }

        return summary
