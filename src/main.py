from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.external.normalizer import normalize_code, explain_strategy
from src.modules.parser import PseudocodeParser
from src.modules.analyzer import ComplexityAnalyzer
import uvicorn
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Orchestrator")

app = FastAPI(title="Analizador de Complejidad Híbrido")

class CodeRequest(BaseModel):
    code: str

@app.post("/analyze")
async def analyze_algorithm(request: CodeRequest):
    response_data = {
        "status": "partial_success", # Asumimos éxito parcial por defecto
        "input_analysis": {},
        "hard_analysis": {"error": "No ejecutado"},
        "soft_analysis": {}
    }

    # --- PASO 1: Normalización ---
    logger.info("1. Normalizando entrada...")
    clean_code = normalize_code(request.code)
    response_data["input_analysis"] = {
        "original_input": request.code,
        "normalized_pascal": clean_code
    }
    
    if not clean_code or "Error" in clean_code:
        # Si falla el normalizador, aquí sí paramos porque no hay código
        raise HTTPException(status_code=400, detail="Error normalizando código")

    # --- PASO 2 y 3: Parser y Analyzer (Bloque Try-Catch Gigante) ---
    math_result = {}
    try:
        logger.info("2. Intentando Parsing y Análisis Matemático...")
        parser = PseudocodeParser()
        ast = parser.parse_text(clean_code)
        
        analyzer = ComplexityAnalyzer()
        math_result = analyzer.analyze(ast)
        
        response_data["hard_analysis"] = math_result
        response_data["status"] = "success" # Si llegamos aquí, todo fue perfecto

    except Exception as e:
        logger.error(f"⚠ El análisis determinista falló: {e}")
        # Guardamos el error pero NO detenemos el programa
        math_result = {
            "cost_expression": "No calculable (Error de sintaxis/estructura)",
            "big_o": "Indeterminado (Ver análisis de IA)",
            "error_details": str(e)
        }
        response_data["hard_analysis"] = math_result
        # No cambiamos status a 'error' fatal, dejamos 'partial_success'

    # --- PASO 4: Consultor de Estrategia (Siempre se ejecuta) ---
    logger.info("4. Consultando estrategia al LLM...")
    # Pasamos el 'clean_code' y el resultado matemático (aunque tenga error)
    strategy_report = explain_strategy(clean_code, math_result)
    response_data["soft_analysis"] = strategy_report

    return response_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)