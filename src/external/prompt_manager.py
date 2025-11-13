"""
Prompt Manager Module

This module centralizes and manages all static prompts used by the
Complexity Analyzer system. It ensures prompt consistency across the
translation and complexity analysis stages handled by the internal LLM.

It provides two main prompt templates:
1. TRANSLATION_PROMPT — Converts user pseudocode (or natural description)
   into the internal pseudocode grammar understood by the deterministic analyzer.
2. COMPLEXITY_PROMPT — Requests the LLM to analyze algorithmic complexity
   and return formal asymptotic notations (O, Ω, Θ).

The prompts are static and deterministic, ensuring reproducibility and
consistency with the analysis pipeline.
"""

from typing import Dict


class PromptManager:
    """
    A simple manager for static and parameterized prompt templates.
    """

    def __init__(self):
        # --- Translation Prompt ---
        self.translation_prompt = (
            "You are part of a hybrid algorithm complexity analysis system. "
            "Your task is to translate the user's pseudocode or natural description "
            "into the internal pseudocode grammar used by the deterministic analyzer.\n\n"
            "Guidelines:\n"
            "- Preserve the algorithm's logic and structure exactly.\n"
            "- Use clear variable names and indentation.\n"
            "- The syntax must match the following conventions:\n"
            "  * Control structures: 'for', 'while', 'if', 'else', 'endif', 'endfor', etc.\n"
            "  * Assignment: '='\n"
            "  * No external libraries or language-specific syntax.\n"
            "  * Use 1-based indexing for arrays.\n\n"
            "Return only the translated pseudocode, without commentary or extra text.\n\n"
            "User input:\n{user_input}\n\n"
            "Output (translated pseudocode):"
        )

        # --- Complexity Analysis Prompt ---
        self.complexity_prompt = (
            "You are an expert in computational complexity theory.\n"
            "Analyze the following pseudocode and determine its asymptotic complexities.\n\n"
            "Instructions:\n"
            "- Carefully derive the time complexity (O), lower bound (Ω), and tight bound (Θ).\n"
            "- If relevant, explain which part dominates the cost (loops, recursion, etc.).\n"
            "- Provide results in formal notation (e.g., O(n log n), Ω(n), Θ(n log n)).\n\n"
            "Pseudocode:\n{pseudocode}\n\n"
            "Return the result in **JSON format** using this exact structure:\n"
            "{\n"
            "  \"O\": \"\",\n"
            "  \"Omega\": \"\",\n"
            "  \"Theta\": \"\",\n"
            "  \"explanation\": \"\"\n"
            "}\n"
            "Do not include any additional commentary."
        )

    def get_translation_prompt(self, user_input: str) -> str:
        """
        Returns the formatted translation prompt.
        """
        return self.translation_prompt.format(user_input=user_input)

    def get_complexity_prompt(self, pseudocode: str) -> str:
        """
        Returns the formatted complexity analysis prompt.
        """
        return self.complexity_prompt.format(pseudocode=pseudocode)

    def get_all_prompts(self) -> Dict[str, str]:
        """
        Returns all static prompt templates (unformatted).
        Useful for debugging or testing.
        """
        return {
            "translation_prompt": self.translation_prompt,
            "complexity_prompt": self.complexity_prompt,
        }
