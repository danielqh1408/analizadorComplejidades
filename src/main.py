"""
Main Orchestrator and API Entry Point (FastAPI)

This module serves as the central orchestrator [cite: ArquitecturaF.png]
for the Complexity Analyzer system. It provides:
1.  A FastAPI backend for API-driven analysis.
2.  A CLI mode for interactive use.

It integrates all core modules:
-   ConfigLoader, Logger, MetricsLogger
-   LLMAssistant (for translation and validation)
-   Lexer, Parser, Analyzer (the deterministic pipeline)

The orchestrator handles the full request lifecycle, including:
-   Input validation (Pydantic)
-   Translation of natural language (if needed)
-   Parallel execution of deterministic analysis (CPU-bound) and
    LLM validation (I/O-bound).
-   Response consolidation and metrics logging.
"""

import asyncio
import sys
import uvicorn
from contextlib import asynccontextmanager
from typing import Optional,Dict, Any, Literal

# --- Framework Imports ---
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from rich import print_json

# --- Project-Specific Imports ---
# Core Services
try:
    from src.services.config_loader import config
    from src.services.logger import get_logger
    from src.services.metrics import metrics_logger
except ImportError as e:
    print(f"FATAL ERROR: Failed to import core services: {e}")
    sys.exit(1)

# External Services
try:
    from src.external.llm_assistant import LLMAssistant
except ImportError as e:
    print(f"FATAL ERROR: Failed to import LLMAssistant: {e}")
    sys.exit(1)

# Deterministic Pipeline Modules
try:
    from src.modules.lexer import Lexer
    from src.modules.parser import PseudocodeParser as Parser # Assuming Parser class
    from src.modules.analyzer import Analyzer # Assuming Analyzer class
except ImportError as e:
    print(f"FATAL ERROR: Failed to import analyzer modules: {e}")
    sys.exit(1)


# --- Global Instances ---
logger = get_logger("Orchestrator")
logger.info("Initializing Orchestrator...")

# Initialize global instances of our services and modules
try:
    llm_assistant = LLMAssistant()
    lexer = Lexer()
    parser = Parser()
    analyzer = Analyzer()
except Exception as e:
    logger.critical(f"Failed to initialize modules: {e}", exc_info=True)
    sys.exit(1)

# --- FastAPI Lifecycle Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    -   Startup: (Currently no action)
    -   Shutdown: Gracefully closes the LLMAssistant's HTTP session.
    """
    logger.info("FastAPI application startup...")
    yield
    # --- Shutdown ---
    logger.info("FastAPI application shutting down...")
    await llm_assistant.close_session()
    logger.info("LLM Assistant session closed.")

app = FastAPI(
    title="Complexity Analyzer API",
    version="1.0.0",
    description="API for deterministic and AI-assisted algorithm complexity analysis.",
    lifespan=lifespan
)

# --- Pydantic API Models ---
class AnalysisRequest(BaseModel):
    """
    Defines the input payload for the /api/analyze endpoint.
    """
    type: Literal["pseudocode", "natural"] = Field(
        ...,
        description="Type of content provided."
    )
    content: str = Field(
        ...,
        description="The pseudocode or natural language text to analyze."
    )

class ComplexityResult(BaseModel):
    """
    Defines the structured output for deterministic complexity.
    """
    O: str = Field(..., example="O(n^2)")
    Omega: str = Field(..., example="Ω(n)")
    Theta: str = Field(..., example="Θ(n^2)")
    raw_expression: str = Field(..., example="n**2 + 2*n + 1")

class AnalysisResponse(BaseModel):
    """
    Defines the final JSON response sent to the client.
    """
    status: Literal["ok", "error"] = "ok"
    type: Literal["pseudocode", "natural"]
    original_content: str
    analyzed_code: Optional[str] = None
    complexity: Optional[ComplexityResult] = None
    llm_validation: Optional[Dict[str, Any]] = None
    token_count: Optional[int] = None
    execution_time_ms: float
    error: Optional[str] = None

# --- Deterministic Pipeline (CPU-Bound) ---

def run_deterministic_analysis(code: str) -> Dict[str, Any]:
    """
    Executes the full, synchronous, CPU-bound analysis pipeline.
    This function is designed to be run in a separate thread via
    `asyncio.to_thread` to avoid blocking the FastAPI event loop.

    Hardware: This task runs entirely on the CPU (Ryzen 7 7700X).
    
    Args:
        code (str): The pseudocode to analyze.

    Returns:
        Dict[str, Any]: A dictionary containing results or an error.
    """
    try:
        logger.info("Deterministic pipeline started...")
        
        # 1. Lexical Analysis
        metrics_logger.start_timer("lexing")
        tokens = lexer.tokenize(code)
        metrics_logger.end_timer("lexing")
        
        # 2. Parsing (Syntax Analysis)
        metrics_logger.start_timer("parsing")
        ast = parser.parse_text(tokens)
        metrics_logger.end_timer("parsing")
        
        # 3. Complexity Analysis (AST Traversal)
        metrics_logger.start_timer("analyzing")
        # analyze() should return a dict, e.g.,
        # {"O": "O(n)", "Omega": "Ω(n)", "Theta": "Θ(n)", "raw": "n"}
        result_dict = analyzer.analyze(ast) 
        metrics_logger.end_timer("analyzing")

        logger.info(f"Deterministic pipeline successful. Complexity: {result_dict.get('O')}")
        
        return {
            "status": "ok",
            "token_count": len(tokens),
            "complexity": result_dict
        }

    except Exception as e:
        logger.error(f"Deterministic pipeline failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": f"AnalysisError: {e}"
        }

# --- Main Orchestration Logic ---

async def run_analysis_pipeline(request: AnalysisRequest) -> Dict[str, Any]:
    """
    The core orchestration function.
    
    1. Handles natural language translation (if needed).
    2. Runs deterministic analysis (CPU-bound) and LLM validation (I/O-bound)
       in parallel [cite: ArquitecturaF.png].
    3. Consolidates results.
    """
    request_timer = "full_request"
    metrics_logger.start_timer(request_timer)
    
    code_to_analyze = request.content
    analyzed_code_source = "original"
    
    # 1. Handle Natural Language Input
    if request.type == "natural":
        logger.info("Natural language detected. Requesting translation...")
        metrics_logger.start_timer("llm_translation")
        try:
            llm_res = await llm_assistant.send_request(
                prompt=f"Translate the following algorithm description into the project's specific pseudocode grammar: {request.content}",
                task_type="translation"
            )
            metrics_logger.end_timer("llm_translation")
            
            if llm_res['status'] == 'error':
                logger.error(f"LLM translation failed: {llm_res['error']}")
                raise ValueError(f"LLM translation failed: {llm_res['error']}")
                
            code_to_analyze = llm_res['content']
            analyzed_code_source = "llm_translated"
            logger.info("Translation successful.")
            
        except Exception as e:
            metrics_logger.end_timer(request_timer)
            return {
                "status": "error",
                "error": str(e),
                "execution_time_ms": metrics_logger.end_timer(request_timer)
            }
            
    # 2. Run Parallel Tasks
    logger.info("Starting parallel analysis (Deterministic + LLM Validation)...")
    
    # Task 1: Deterministic (CPU-bound)
    # We MUST run this in a thread pool to avoid blocking the event loop.
    # This fully utilizes the Ryzen 7 7700X cores.
    deterministic_task = asyncio.to_thread(run_deterministic_analysis, code_to_analyze)
    
    # Task 2: LLM Validation (I/O-bound)
    validation_prompt = (
        f"Validate the following pseudocode and provide its "
        f"Big O, Big Omega, and Big Theta complexity: \n\n{code_to_analyze}"
    )
    llm_task = llm_assistant.send_request(
        prompt=validation_prompt,
        task_type="validation"
    )
    
    # Wait for both tasks to complete
    try:
        results = await asyncio.gather(deterministic_task, llm_task)
        det_result, llm_result = results
    except Exception as e:
        # Catch any unexpected errors during parallel execution
        logger.critical(f"Unhandled parallel execution error: {e}", exc_info=True)
        metrics_logger.end_timer(request_timer)
        return {
            "status": "error",
            "error": f"Orchestration failure: {e}",
            "execution_time_ms": metrics_logger.end_timer(request_timer)
        }

    # 3. Consolidate and Format Response
    logger.info("Parallel tasks complete. Consolidating results.")
    
    final_response = {
        "status": "ok",
        "type": request.type,
        "original_content": request.content,
        "analyzed_code": code_to_analyze if analyzed_code_source == "llm_translated" else None,
        "complexity": None,
        "llm_validation": llm_result,
        "token_count": None,
        "error": None
    }
    
    if det_result['status'] == 'ok':
        raw_comp = det_result['complexity']
        final_response['complexity'] = {
            "O": raw_comp.get('O', 'N/A'),
            "Omega": raw_comp.get('Omega', 'N/A'),
            "Theta": raw_comp.get('Theta', 'N/A'),
            "raw_expression": raw_comp.get('raw', 'N/A')
        }
        final_response['token_count'] = det_result['token_count']
    else:
        final_response['error'] = det_result['error']
        final_response['status'] = 'error' # Mark final status as error if pipeline failed

    # Stop final timer and save all metrics
    final_response['execution_time_ms'] = metrics_logger.end_timer(request_timer)
    if config.get_bool('PERFORMANCE', 'enable_metrics', default=False):
        metrics_logger.save() # Persist metrics

    return final_response

# --- API Endpoint ---

@app.post("/api/analyze", response_model=AnalysisResponse)
async def api_analyze_code(request: AnalysisRequest):
    """
    FastAPI endpoint to analyze algorithm complexity.
    
    Receives a JSON payload, orchestrates the analysis pipeline,
    and returns a consolidated JSON response.
    """
    logger.info(f"Received API request. Type: {request.type}")
    
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Field 'content' cannot be empty.")
        
    result_data = await run_analysis_pipeline(request)
    
    if result_data['status'] == 'error' and not result_data.get('complexity'):
        # If the whole pipeline failed (e.g., translation)
        raise HTTPException(status_code=500, detail=result_data['error'])
        
    return AnalysisResponse(**result_data)

# --- CLI Mode ---

async def cli_mode():
    """
    Runs the analyzer in a simple command-line interface mode.
    """
    logger.info("--- Complexity Analyzer (CLI Mode) ---")
    print("\n--- Analizador de Complejidad (Modo CLI) ---")
    print("Ingrese el pseudocódigo. Presione Ctrl+D (Linux/macOS) o Ctrl+Z+Enter (Windows) para finalizar.")
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
        
    code = "\n".join(lines)
    
    if not code.strip():
        logger.warning("No input provided. Exiting.")
        print("\nNo se ingresó código.")
        await llm_assistant.close_session() # Ensure session is closed
        return

    print("\nAnalizando...")
    
    request_data = AnalysisRequest(type="pseudocode", content=code)
    result = await run_analysis_pipeline(request_data)
    
    print("\n--- Resultado del Análisis ---")
    print_json(data=result)
    
    # Clean up the session
    await llm_assistant.close_session()

# --- Entry Point ---

if __name__ == "__main__":
    """
    Main entry point.
    -   Runs in CLI mode if '--cli' is passed.
    -   Runs as a Uvicorn server otherwise.
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        try:
            asyncio.run(cli_mode())
        except KeyboardInterrupt:
            logger.info("CLI mode interrupted by user. Exiting.")
    else:
        try:
            host = config.get('API', 'host', default='127.0.0.1')
            port = config.get_int('API', 'port', default=8000)
            workers = config.get_int('API', 'workers', default=1)
            
            logger.info(f"Starting FastAPI server at http://{host}:{port} with {workers} worker(s)...")
            
            uvicorn.run(
                "main:app", 
                host=host, 
                port=port, 
                workers=workers,
                reload=True if config.get('ENVIRONMENT', 'mode') == 'development' else False
            )
        except Exception as e:
            logger.critical(f"Failed to start Uvicorn server: {e}", exc_info=True)