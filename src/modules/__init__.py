"""
Deterministic Analyzer Modules Sub-package

This package contains the core deterministic pipeline for
analyzing pseudocode complexity.
"""

# Import main classes from each module
try:
    from .lexer import Lexer
    from .parser import PseudocodeParser as Parser # Use clear alias
    from .analyzer import Analyzer
except ImportError:
    print("Warning: Deterministic modules (Lexer, Parser, Analyzer) could not be imported.")

# Define what 'from src.modules import *' will import
__all__ = [
    "Lexer",
    "Parser",
    "Analyzer"
]