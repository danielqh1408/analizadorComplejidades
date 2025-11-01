🧯 Complexity Analyzer — Troubleshooting & FAQ
🧩 Overview

This document lists common issues encountered during installation, execution, testing, or API interaction in the Complexity Analyzer Project, along with their most probable causes and recommended solutions.

The guide is meant for developers, testers, and maintainers working with the local Python environment or the LLM-connected backend.

⚙️ 1. Installation & Environment Issues
❌ Issue	🔍 Cause	🧩 Solution
ModuleNotFoundError	Running scripts from the wrong directory or missing __init__.py	Always run commands from the project root. Make sure each package folder (modules, services, etc.) contains an empty __init__.py file.
ImportError: No module named 'src'	Python path not set correctly	Add project root to PYTHONPATH:
set PYTHONPATH=%cd% (Windows)
export PYTHONPATH=$(pwd) (Linux/Mac).
pip install fails or dependency not found	Outdated pip or missing build tools	Run:
python -m pip install --upgrade pip
pip install wheel setuptools
Numba/CuPy installation errors	Incompatible CUDA or Python version	Ensure CUDA 12.x is installed. Use Python 3.11 and the compatible cupy-cuda12x==12.1.0, numba==0.58.1.
Sympy import errors	Incomplete installation	Reinstall dependencies: pip install sympy==1.12
🧠 2. Runtime Errors
❌ Issue	🔍 Cause	🧩 Solution
SyntaxError during parsing	Invalid pseudocode syntax	Ensure pseudocode follows defined grammar rules (e.g., FOR i ← 1 TO n DO ... END FOR). Use uppercase keywords and balanced structures.
KeyError in analyzer	Undefined AST node type	Verify that every AST node has a corresponding visitor method (visit_AssignNode, etc.) in analyzer.py.
AttributeError: NoneType	Parser returned invalid AST	Run the Lexer test first to confirm valid tokens. Then ensure Parser builds a non-empty root node.
TypeError: unsupported operand type(s)	Mixing symbolic and numeric types	Ensure symbolic variables are handled through sympy.Symbol and numeric constants through standard Python types.
FileNotFoundError	Wrong file path in I/O	Always use relative paths inside src/services/file_io.py. Example: read_file("data/example.pseudo").
RecursionError	Infinite recursion during analysis	Check Analyzer’s recursion handling or ensure base case detection is implemented in recurrence resolution.
⚡ 3. Performance & GPU Issues
❌ Issue	🔍 Cause	🧩 Solution
Slow execution	Running in CPU-only mode	Verify GPU availability:
python -m cupy.show_config
If not detected, reinstall CUDA Toolkit 12.x.
CUDA driver not found	Outdated NVIDIA driver	Install latest drivers from NVIDIA Downloads
.
numba.cuda.cudadrv.error.CudaSupportError	Incompatible CUDA runtime	Match CuPy and Numba versions with your CUDA runtime. Use:
cupy-cuda12x==12.1.0, numba==0.58.1.
cupy fallback to CPU	CuPy failed to initialize GPU	Force device initialization:
import cupy; cupy.cuda.Device(0).use()
RAM overflow	Large symbolic expansions	Use sympy.simplify() or break recurrence trees into subproblems before evaluation.
CPU underutilization	Multiprocessing not activated	Use parallel mode in Analyzer:
@njit(parallel=True) and joblib.Parallel for loop-heavy analysis.
🧮 4. API & LLM Connection Problems
❌ Issue	🔍 Cause	🧩 Solution
401 Unauthorized (Gemini/OpenAI)	Missing or invalid API key	Check your environment variables:
echo %GEMINI_API_KEY% or echo $OPENAI_API_KEY.
TimeoutError during LLM calls	Slow connection or large payload	Increase timeout in llm_wrapper.py:
timeout=aiohttp.ClientTimeout(total=60)
RateLimitError	Too many LLM requests	Implement exponential backoff or delay retry logic in API wrapper.
ValueError: Invalid JSON response	LLM response is malformed	Add schema validation and fallback parsing in the Extractor component.
aiohttp.ClientConnectorError	No internet or firewall blocking	Check your connection and proxy settings.
SSL: CERTIFICATE_VERIFY_FAILED	SSL misconfiguration	Add parameter ssl=False in local test environments only. Do not disable SSL in production.
🧪 5. Testing & CI/CD Issues
❌ Issue	🔍 Cause	🧩 Solution
pytest can’t find tests	Missing __init__.py or wrong path	Make sure tests/ has __init__.py and run tests from root: pytest tests/.
ImportError inside tests	Relative imports used incorrectly	Use absolute imports: from src.modules import parser instead of from ..modules.
Coverage < 90%	Missing tests for some functions	Review pytest --cov-report=term-missing and add unit tests for uncovered methods.
CI/CD build fails	Workflow misconfigured	Ensure .github/workflows/ci.yml is valid YAML and branch name matches main or dev.
Linting errors	Non-PEP8 compliant code	Run: flake8 src --max-line-length=120 and fix all warnings.
🧰 6. Logging & Metrics
❌ Issue	🔍 Cause	🧩 Solution
No logs appear	logger not initialized	Ensure get_logger(__name__) is called before logging.
File logging not working	Disabled in config.ini	Check [LOGGING] enable_file_logging = true.
Metrics file empty	Analyzer didn’t complete	Check for exceptions before metric save. Logs should indicate cause.
Timestamps missing	Custom handler overwriting format	Verify formatter in logger.py includes %(asctime)s.
🧩 7. Configuration & Environment Variables
❌ Issue	🔍 Cause	🧩 Solution
config.ini not found	Wrong working directory	Always execute from project root where config.ini exists.
ValueError: invalid literal for int()	Malformed numeric field in config.ini	Verify integer fields like max_concurrent_requests have valid numbers.
API keys not loaded	Incorrect environment variable names	Use GEMINI_API_KEY and OPENAI_API_KEY exactly as defined in [SECURITY] section.
KeyError loading config	Missing section or key	Ensure config.ini follows required format: [API], [LLM], [LOGGING], [SECURITY].
🧱 8. Common Debugging Commands
Purpose	Command
Show current Python path	import sys; print(sys.path)
Reinstall dependencies	pip install -r requirements.txt --force-reinstall
Check CUDA devices	python -m cupy.show_config
Run analyzer in debug mode	python src/modules/analyzer.py --debug
View live logs	tail -f logs/app.log
Clear cache and bytecode	find . -name "__pycache__" -type d -exec rm -r {} +
🧭 9. Advanced Debug Techniques
🔹 Enable Debug Logging

Edit config.ini:

[LOGGING]
log_level = DEBUG
enable_console_logging = true
enable_file_logging = true


This provides detailed step-by-step logs for Lexer, Parser, and Analyzer modules.

🔹 Trace Function Execution

Add:

import trace
tracer = trace.Trace(trace=True)
tracer.run('your_function_call()')


This helps track logic flow through nested calls.

🔹 Profile Performance
python -m cProfile -o profile.out src/modules/analyzer.py
snakeviz profile.out

🔹 Monitor GPU Memory
import cupy
print(cupy.cuda.runtime.memGetInfo())

🧠 10. Recovery Steps

If the system becomes unstable or configuration is corrupted:

Delete compiled caches:

rmdir /s /q __pycache__
del logs/*.log


Reinstall dependencies:

pip install -r requirements.txt --force-reinstall


Reset environment variables:

setx GEMINI_API_KEY ""
setx OPENAI_API_KEY ""


Recreate config.ini from backup in docs/config_template.ini.

Restart Uvicorn:

uvicorn src.main:app --reload

✅ 11. Quick Verification Checklist
Checkpoint	Expected
Lexer produces tokens	✅ Recognizes all keywords
Parser builds AST	✅ Returns root SequenceNode
Analyzer runs successfully	✅ Outputs O, Ω, Θ
Logger active	✅ Timestamped entries in logs/app.log
LLM connectivity	✅ Gemini or OpenAI responds
Metrics collected	✅ metrics.json updated
Tests pass	✅ pytest shows all PASSED
GPU acceleration	✅ Detected by CuPy
Config valid	✅ No missing fields
🧩 12. Support & Reporting

If you encounter issues not listed here:

Check existing GitHub Issues tab.

Include:

Error message and traceback.

Python version.

Operating system.

Steps to reproduce.

Tag your issue appropriately: bug, performance, API, or parser.

✅ Summary

This guide provides all known solutions for:

Environment setup issues

Runtime or parser errors

GPU acceleration problems

LLM connectivity failures

Logging and metric inconsistencies

By following this reference, developers can quickly diagnose and correct any malfunction while maintaining stability and performance across the Complexity Analyzer system.