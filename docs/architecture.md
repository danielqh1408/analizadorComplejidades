🧩 Complexity Analyzer — System Architecture
📖 Overview

The Complexity Analyzer Project is a modular system designed to analyze algorithmic complexity (O, Ω, Θ) from pseudocode or natural language inputs.
It combines deterministic analysis (Lexer → Parser → Analyzer) with LLM-assisted reasoning (Gemini / OpenAI), providing a complete hybrid system for computational complexity evaluation and validation.

The system is implemented in Python 3.11, optimized for multi-core CPUs (Ryzen 7 7700X) and CUDA GPUs (RTX 4060 Ti) using:

Numba for JIT acceleration

CuPy for GPU-based numerical computation

SymPy for symbolic math and recurrence resolution

FastAPI for backend API services

🏗️ Architecture Overview

The project follows a 3-layer architecture pattern, ensuring modularity, scalability, and maintainability:

+------------------------------------------------------------+
| PRESENTATION LAYER |
| (Frontend: InputPanel, ControlPanel, ResultsDisplay) |
| |
| - User enters pseudocode or natural language input. |
| - Sends request to FastAPI endpoint /api/analyze. |
+------------------------------------------------------------+
| LOGIC / BACKEND LAYER |
| (Core Engine, Orchestrator, LLM Assistant) |
| |
| - API Gateway (FastAPI) handles request flow. |
| - Deterministic Analyzer executes via Lexer → Parser → |
| AST Engine. |
| - LLM Assistant (Gemini/OpenAI) performs reasoning, |
| translation, and validation. |
| - Results are consolidated, formatted, and returned. |
+------------------------------------------------------------+
| EXTERNAL SERVICES LAYER |
| (Gemini / OpenAI API, Metrics, Logging, Config Loader) |
| |
| - Handles all external interactions and persistent data. |
| - Includes logging, metrics recording, and configuration. |
+------------------------------------------------------------+

🧠 Core Components
Layer	Component	Purpose
Frontend	InputPanel	Captures pseudocode or natural language input.
	ControlPanel	Sends input via API; shows status and metrics.
	ResultsDisplay	Displays parsed tokens, AST diagram, and complexity results.
Backend	main.py	FastAPI application entry point and orchestrator.
	Lexer	Tokenizes pseudocode into recognized lexical units.
	Parser	Constructs Abstract Syntax Tree (AST) based on grammar rules.
	Analyzer	Traverses AST (AST Walker) to compute O, Ω, Θ.
	LLMAssistant	Communicates with Gemini/OpenAI for reasoning, translation, and validation.
Services	ConfigLoader	Singleton configuration loader from config.ini.
	Logger	Centralized structured logging system.
	MetricsLogger	Records and stores performance metrics (latency, tokens, etc.).
External	Gemini API	Provides reasoning and validation for pseudocode and natural language.
	OpenAI API	Alternative LLM provider.
⚙️ Data Flow

Input Phase

The user provides an algorithm in pseudocode or natural language.

The frontend sends a JSON request to the API endpoint /api/analyze.

Processing Phase (Backend)

The Orchestrator receives the request and determines its type (pseudocode or natural).

It launches two parallel flows:

Deterministic flow: Lexer → Parser → AST → Analyzer.

LLM flow: Gemini/OpenAI reasoning and validation.

Both results are combined into a unified response with metrics.

Output Phase

Results are formatted as JSON:

{
  "status": "ok",
  "type": "pseudocode",
  "tokens": 123,
  "complexity": { "O": "O(n log n)", "Ω": "Ω(n)", "Θ": "Θ(n log n)" },
  "llm_validation": "Matches theoretical complexity",
  "execution_time_ms": 25.4
}

🔍 Deterministic Analysis Flow

Lexer → Parser → AST Engine → Analyzer

Stage	Description	Output
Lexer	Scans pseudocode and produces tokens.	Token list
Parser	Validates grammar and builds an AST.	Abstract Syntax Tree
AST Engine / Analyzer	Traverses the AST and applies complexity rules (Cormen, Bisbal).	Complexity metrics
Example:

Input pseudocode:

FOR i 🡨 1 TO n DO
    sum 🡨 sum + i
END FOR


Output analysis:

O(n), Ω(n), Θ(n)

🤖 LLM-Assisted Reasoning

The LLMAssistant uses Gemini or OpenAI APIs to:

Translate natural language descriptions into pseudocode.

Validate that the deterministic analysis aligns with theoretical reasoning.

Generate explanations and diagrams.

It uses asynchronous calls via aiohttp for parallel execution and integrates with:

MetricsLogger → Measures latency and token cost.

ConfigLoader → Reads API endpoints and keys.

Logger → Logs request and response summaries.

🧰 Optimization & Performance
CPU Optimization

Numba JIT Compilation accelerates numerical operations in complexity calculations.

Multiprocessing / Joblib runs Lexer, Parser, and Analyzer tasks in parallel across CPU cores.

GPU Optimization

CuPy CUDA 12.x offloads matrix operations and symbolic expansions when analyzing large ASTs.

Numba CUDA Kernels are used for recurrence resolution acceleration.

Memory Optimization

Numpy arrays replace Python lists in large loops.

Avoids unnecessary data copies by using memory views.

📈 Metrics & Logging
Component	Function
Logger	Provides timestamped logs for every event.
MetricsLogger	Tracks latency, execution time, token counts, and throughput.
ConfigLoader	Centralized access to runtime configuration.

Example log:

[INFO] Lexer completed in 12.4 ms — 186 tokens
[METRICS] Analyzer total time: 25.4 ms
[LLM] Response from Gemini: 1.32s, 512 tokens

🧩 Configuration

All configurations are handled via config.ini.

Example:

[API]
host = 127.0.0.1
port = 8000
max_concurrent_requests = 8

[LLM]
primary_provider = gemini
gemini_model = gemini-pro
gemini_api_base_url = https://generativelanguage.googleapis.com/v1beta/models
openai_model = gpt-4-turbo

[SECURITY]
gemini_api_key_env = GEMINI_API_KEY
openai_api_key_env = OPENAI_API_KEY

🧪 Testing & Validation

All modules include automated tests under /tests/, implemented with pytest.

Test File	Purpose
test_lexer_parser.py	Validates tokenization and AST construction.
test_analyzer.py	Verifies correctness of complexity analysis.
test_main_api.py	Ensures FastAPI endpoint works end-to-end.
test_metrics.py	Confirms accuracy and thread-safety of metrics.

Tests are executed via CI/CD on every push or pull request.

🔄 CI/CD Integration

GitHub Actions pipeline performs:

Dependency installation.

Linting and static analysis.

Full pytest run with coverage report.

Build and deployment (if all tests pass).

Example pipeline stages:
Build → Test → Lint → Deploy

🧭 Design Principles
Principle	Description
Modularity	Each module is self-contained and testable.
Scalability	Designed for multicore and GPU scaling.
Transparency	All computations are logged and measurable.
Extendability	New grammars or LLMs can be integrated easily.
Reliability	Automatic tests ensure consistent correctness.
📚 Theoretical Foundations

This project is based on:

Introduction to Algorithms (Cormen, Leiserson, Rivest, Stein) — 4th Edition.

Manual de Algorítmica, Recursividad, Complejidad y Diseño de Algoritmos (Bisbal Riera).

Both works inform the rules applied in:

Complexity calculation

Recurrence relations

Case-based analysis (best, worst, average)

🧱 Future Extensions

Graphical visualization of AST and flow diagrams.

Web frontend with real-time feedback.

Integration with a local knowledge base for offline reasoning.

Parallel LLM ensemble (cross-validation of models).

Web-based benchmark dashboard.

✅ Summary

The Complexity Analyzer Project is a high-performance, modular system that merges deterministic computation with intelligent reasoning.
It leverages modern hardware, strong theoretical grounding, and automated testing to ensure precision, speed, and maintainability.

Determinism + Reasoning = Verified Algorithmic Insight