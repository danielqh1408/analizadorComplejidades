⚙️ Complexity Analyzer — Execution & Validation Guide
📦 1. Environment Setup

Before running or testing the system, make sure you have the proper environment configured.

🧰 Requirements

Python: 3.11 (64-bit)

Pip: latest version

GPU: NVIDIA RTX 4060 Ti (CUDA 12.x)

CPU: AMD Ryzen 7 7700X (8 cores / 16 threads)

RAM: DDR5 (32 GB recommended)

🧩 Dependencies

All required libraries are defined in requirements.txt.

Install them with:

pip install -r requirements.txt

🧠 Verify installation

Check Python and package versions:

python --version
pip show numpy numba sympy fastapi uvicorn


Expected output (approximate):

Python 3.11.x
numpy 1.26.4
numba 0.58.1
sympy 1.12
fastapi 0.115.0
uvicorn 0.30.1

🗂️ 2. Project Structure
complexity-analyzer/
│
├── src/
│   ├── main.py
│   ├── modules/
│   │   ├── lexer.py
│   │   ├── parser.py
│   │   ├── ast_nodes.py
│   │   ├── analyzer.py
│   ├── services/
│   │   ├── config_loader.py
│   │   ├── logger.py
│   │   ├── metrics.py
│   │   ├── file_io.py
│   └── orchestrator/
│       ├── orchestrator.py
│       └── llm_wrapper.py
│
├── tests/
│   ├── test_lexer_parser.py
│   ├── test_analyzer.py
│   ├── test_main_api.py
│   └── test_metrics.py
│
├── docs/
│   ├── architecture.md
│   ├── developer_guide.md
│   ├── execution.md
│
├── requirements.txt
├── config.ini
└── README.md

🚀 3. Running the Application
🧩 Step 1 — Load Environment Variables

Before starting, make sure your LLM API keys are set as environment variables:

setx GEMINI_API_KEY "your_api_key_here"


(Use export instead of setx on Linux/Mac.)

🧩 Step 2 — Launch the Backend API

Run the backend using Uvicorn:

uvicorn src.main:app --reload --host 127.0.0.1 --port 8000


Expected console output:

INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.

🧩 Step 3 — Test the API Endpoint

Use curl, Postman, or your browser to send a request:

curl -X POST "http://127.0.0.1:8000/api/analyze" ^
     -H "Content-Type: application/json" ^
     -d "{\"type\": \"pseudocode\", \"content\": \"FOR i 🡨 1 TO n DO sum 🡨 sum + i END FOR\"}"


Expected JSON response:

{
  "status": "ok",
  "type": "pseudocode",
  "complexity": { "O": "O(n)", "Ω": "Ω(n)", "Θ": "Θ(n)" },
  "execution_time_ms": 12.3,
  "llm_validation": "Matches theoretical complexity"
}

🧪 4. Running Unit Tests

All tests are located under /tests and can be executed with pytest.

🔹 Run all tests:
pytest -v

🔹 Run a specific test:
pytest tests/test_analyzer.py -v

🔹 Generate coverage report:
pytest --cov=src --cov-report=term-missing


Expected example:

---------- coverage: platform win32, python 3.11 ----------
Name                               Stmts   Miss  Cover
--------------------------------------------------------
src/modules/analyzer.py               92      4    95%
src/modules/parser.py                 85      3    96%
src/services/logger.py                47      0   100%
--------------------------------------------------------
TOTAL                                327      7    97%

📊 5. Verifying System Components
✅ 5.1. Lexer

Command:

python -m src.modules.lexer tests/examples/simple_for.pseudo


Expected:

[INFO] Lexer completed — 14 tokens

✅ 5.2. Parser

Command:

pytest tests/test_parser.py -v


Expected:

Parser correctly builds AST with 1 root node and 2 nested loops.

✅ 5.3. Analyzer

Command:

pytest tests/test_analyzer.py -v


Expected:

Detected complexity: O(n log n), Ω(n), Θ(n log n)

✅ 5.4. LLM Integration (Optional)

Command:

python src/orchestrator/llm_wrapper.py --test


Expected:

LLM connection established — Gemini response: valid

🔍 6. Logs & Metrics
📁 Logs

All runtime logs are stored in:

logs/app.log


Typical log entry:

[2025-11-01 14:22:04] [INFO] [Analyzer]: Completed O/Ω/Θ evaluation in 12.5 ms

📊 Metrics

Generated metrics (time, tokens, latency) are stored in:

logs/metrics.json


To view metrics in console:

python src/services/metrics.py --view

🧮 7. GPU & Performance Validation

To validate that your GPU and multithreading optimizations are working:

🧩 GPU computation test
python -m src.modules.analyzer --gpu-test


Expected:

GPU acceleration (CUDA 12.x) active — execution speed: 1.82x faster

🧩 CPU multithreading test
python -m src.modules.analyzer --cpu-test


Expected:

CPU cores utilized: 16 — average analysis time: 8.2 ms

🧠 8. Troubleshooting
Issue	Cause	Solution
ModuleNotFoundError	Wrong project root	Run commands from the project’s root directory.
LLM API error	Invalid or missing key	Check environment variables (GEMINI_API_KEY / OPENAI_API_KEY).
Test import error	Wrong Python path	Add project root to PYTHONPATH.
Slow execution	CPU mode only	Check if CUDA driver is installed.
No logs appear	Config path issue	Verify config.ini [LOGGING] section.
🧩 9. Full Validation Checklist

✅ Lexer recognizes all pseudocode structures
✅ Parser builds a valid AST hierarchy
✅ Analyzer computes O, Ω, Θ accurately
✅ Metrics and logs recorded successfully
✅ API endpoint /api/analyze responds correctly
✅ Tests (pytest) all pass with >90% coverage
✅ GPU acceleration validated
✅ Configuration and logging functional

🏁 10. Clean Shutdown

When finished testing:

CTRL + C


Then clear any compiled or cache files:

python -m compileall -b src
rmdir /s /q __pycache__

✅ Summary

This guide provides the complete procedure for:

Installing dependencies

Running the backend API

Executing local unit tests

Validating CPU/GPU performance

Checking logs and metrics

Once all validations pass, the system is considered ready for CI/CD integration and production deployment.