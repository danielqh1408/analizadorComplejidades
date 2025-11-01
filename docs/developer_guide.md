🧠 Complexity Analyzer — Developer Guide
🧩 Overview

This guide is intended for developers contributing to or extending the Complexity Analyzer Project.
It provides a detailed explanation of the internal architecture, coding standards, workflows, and extension points.

The system follows a deterministic + LLM hybrid model, combining algorithmic parsing and AST-based complexity computation with reasoning and validation from Gemini or OpenAI.

⚙️ 1. Core Design Principles

The following principles define the design and coding standards of this project:

Principle	Description
Modularity	Each module serves one clear purpose. Avoid circular dependencies.
Performance	Always aim for O(n) or better complexity inside core analysis.
Scalability	Code must scale with multicore CPU and CUDA GPU acceleration.
Clarity	Maintain clean, commented, and readable code.
Transparency	All major operations must be logged using the logger module.
Testability	Each component should include at least one pytest validation.
🧱 2. Project Layer Overview

The architecture is composed of three main layers:

Layer	Modules	Purpose
Frontend (Presentation)	InputPanel, ControlPanel, ResultsDisplay	Provides user interface for input and visualization.
Backend (Logic)	Lexer, Parser, Analyzer, Orchestrator	Core logic: analysis, grammar validation, complexity computation.
External Services	LLM Wrapper, Logger, ConfigLoader, Metrics	Interfaces with Gemini/OpenAI APIs and handles system-level services.

All code resides under the src/ directory:

src/
├── modules/        → Lexer, Parser, Analyzer, AST structures
├── services/       → Logging, Metrics, ConfigLoader, FileIO
├── orchestrator/   → API and task controller
└── main.py         → FastAPI entry point

🧩 3. Module Development Guide
🔹 3.1 Lexer (lexer.py)

Purpose: Convert pseudocode into tokens.

Class: Lexer

Method: tokenize(text: str) -> list[Token]

Output: list of token objects

Tip: Use regex for pattern matching.

Test file: tests/test_lexer_parser.py

Extending the Lexer

Add new token patterns to handle new language constructs (e.g., REPEAT-UNTIL).

Update tests accordingly.

🔹 3.2 Parser (parser.py)

Purpose: Build an Abstract Syntax Tree (AST) based on the grammar.

Class: Parser

Method: parse(tokens: list) -> ASTNode

Uses grammar rules defined in file_io.py or grammar definition files.

AST node types defined in ast_nodes.py.

Extending the Parser

Add new grammar rules for control structures or data operations.

Create new ASTNode subclasses for new structures.

Validate with pytest tests/test_parser.py.

🔹 3.3 AST Nodes (ast_nodes.py)

Purpose: Define structure and hierarchy of algorithmic constructs.

Base class: ASTNode

Derived classes: AssignNode, LoopNode, ConditionalNode, CallNode, SequenceNode

Each node implements accept(visitor) for the Visitor pattern.

Adding New Node Types

Create new class extending ASTNode.

Add its handling in Analyzer’s visit_* methods.

Update diagram visualization in the frontend if applicable.

🔹 3.4 Analyzer (analyzer.py)

Purpose: Traverse AST and compute time complexity (O, Ω, Θ).

Class: Analyzer

Method: analyze(ast: ASTNode) -> dict

Uses symbolic math (sympy) for recurrence solving.

Accelerated via numba or cupy for heavy computation.

Returns dictionary of complexity classes.

Extending the Analyzer

Add new rules for pattern detection (divide & conquer, dynamic programming, etc.).

Update symbolic recurrence solver if new recursion types appear.

Use logging and metrics for every analysis.

🔹 3.5 Orchestrator (orchestrator.py)

Purpose: Manage the full request flow between deterministic analysis and LLM validation.

Receives request from main.py via FastAPI.

Runs Lexer → Parser → Analyzer pipeline.

Calls LLM Assistant in parallel (Gemini or OpenAI).

Consolidates and formats results.

Extending the Orchestrator

Add support for multiple input languages.

Integrate caching or concurrency controls.

Extend JSON output schema as needed.

🔹 3.6 LLM Assistant (llm_wrapper.py)

Purpose: Interface with Gemini and OpenAI APIs for reasoning, translation, and validation.

Async-based using aiohttp.

Functions:

translate_natural_language()

validate_complexity()

generate_explanation()

Adding a New LLM Provider

Create a subclass LLMProviderBase.

Implement API calls, headers, and payload structure.

Register in the orchestrator.

🔹 3.7 Services (logger.py, config_loader.py, metrics.py, file_io.py)

These provide global system utilities:

File	Role
logger.py	Centralized logging system using RichHandler.
config_loader.py	Loads values from config.ini and caches them.
metrics.py	Measures latency, token count, and GPU/CPU utilization.
file_io.py	Safe read/write JSON/text utilities.
🧪 4. Testing and Validation

All tests are written with pytest.

🔹 Run all tests
pytest -v

🔹 Run with coverage
pytest --cov=src --cov-report=term-missing

🔹 Add a new test

Add file: tests/test_<module>.py

Use pytest.mark.parametrize for multiple cases.

Follow naming conventions:

Test functions: test_<function_name>()

Fixtures: setup_<context>()

🧩 5. Logging & Debugging

Use logger for structured output:

from src.services.logger import get_logger
logger = get_logger(__name__)
logger.info("Parser initialized successfully")

Log levels

DEBUG → Detailed computation info.

INFO → Standard operation logs.

WARNING → Recoverable issues.

ERROR → Failures needing attention.

Logs are written to logs/app.log and formatted with timestamps and module names.

⚙️ 6. Performance Optimization
CPU-Level

Use Numba JIT (@njit(parallel=True)) for loops or recursion-heavy tasks.

Use Joblib or Multiprocess for parallel task distribution.

GPU-Level

Use CuPy for heavy matrix operations or AST evaluations.

Use Numba CUDA kernels for symbolic recurrence resolution.

Memory

Prefer NumPy arrays over Python lists.

Minimize deep copies (use view() and in-place ops).

🧮 7. Extending Complexity Rules

Rules follow theoretical models from Cormen (CLRS) and Bisbal Riera:

Construct	Example	Complexity
Assignment	x ← x + 1	O(1)
Loop	FOR i ← 1 TO n	O(n)
Nested Loop	Two nested loops	O(n²)
Conditional	IF / ELSE	max(branches)
Recursion	T(n) = aT(n/b) + f(n)	Use Master Theorem

To add new rule:

Add detection in Analyzer.visit_*().

Update recurrence solver.

Extend tests under test_analyzer.py.

🚀 8. Deployment & Execution

See full execution steps in docs/execution.md.

Basic run command:

uvicorn src.main:app --reload


Run local analysis:

python src/modules/analyzer.py --test


Run LLM integration:

python src/orchestrator/llm_wrapper.py --test

🔄 9. Version Control Workflow

Recommended branching strategy:

Branch	Purpose
main	Stable production code
dev	Development and testing
feature/*	New features or modules
hotfix/*	Urgent bug fixes

Commit format:

[Module] — Description


Example:

[Analyzer] — Added recursive detection for merge sort pattern

🧰 10. CI/CD Integration (Future)

CI/CD pipeline (GitHub Actions) will:

Install dependencies

Run linting (flake8)

Execute pytest

Generate coverage report

Configuration file: .github/workflows/ci.yml

You can enable it after local validation is complete.

🧩 11. Contribution Guidelines
Coding Style

Follow PEP 8 conventions.

Max line length: 120 characters.

Use type hints and docstrings.

Functions must explain:

Purpose

Inputs/outputs

Computational method used

Reason for algorithmic choice

Documentation

Each new module or feature must update:

docs/architecture.md

docs/execution.md

docs/developer_guide.md

Review Process

Create a feature branch.

Commit and push changes.

Open a pull request into dev.

Pass all tests and review before merging to main.

✅ 12. Summary

This guide provides the technical roadmap for:

Understanding module interactions

Extending analytical and LLM components

Following clean and efficient coding practices

Maintaining system performance across CPU/GPU

Testing and contributing with confidence

The Complexity Analyzer is designed to evolve —
each extension, optimization, or new complexity rule brings it closer to a complete intelligent analysis engine.