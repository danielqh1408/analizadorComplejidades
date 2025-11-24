"""
Deterministic Analyzer Modules Sub-package

This package contains the core deterministic pipeline for
analyzing pseudocode complexity.
"""

# Import main classes from each module
try:
    from .parser import PseudocodeParser as Parser # Use clear alias
except ImportError:
    print("Warning: Deterministic modules (Parser) could not be imported.")

# Define what 'from src.modules import *' will import
__all__ = [
    "Parser"
]