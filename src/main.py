from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.external.normalizer import normalize_code, explain_strategy
from src.modules.parser import PseudocodeParser
from src.modules.analyzer import ComplexityAnalyzer
import uvicorn
import logging
import os
from dotenv import load_dotenv

# Carga .env y configura log básico
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Orchestrator")

app = FastAPI(title="Analizador de Complejidad Híbrido")

class CodeRequest(BaseModel):
    code: str

@app.post("/analyze")
async def analyze_algorithm(request: CodeRequest):
    response_data = {
        "status": "partial_success",
        "input_analysis": {},
        "hard_analysis": {"error": "No ejecutado"},
        "soft_analysis": {},
        "ast_debug": None
    }

    # 1. Normalización
    logger.info("1. Normalizando entrada...")
    clean_code = normalize_code(request.code)
    response_data["input_analysis"] = {
        "original_input": request.code,
        "normalized_pascal": clean_code
    }
    
    if not clean_code or "Error" in clean_code:
        raise HTTPException(status_code=400, detail="Error normalizando código")

    # 2. Parsing y Análisis
    math_result = {}
    try:
        logger.info("2. Parsing y Análisis...")
        parser = PseudocodeParser()
        ast_objects = parser.parse_text(clean_code) # Esto devuelve una lista de FunctionNode
        
        # Serializar AST para el Frontend
        # Como parse_text devuelve una lista de funciones
        ast_json = [func.to_dict() for func in ast_objects]
        response_data["ast_debug"] = ast_json

        # Análisis Matemático
        analyzer = ComplexityAnalyzer()
        if ast_objects:
            # Analizamos la primera función encontrada como punto de entrada
            math_result = analyzer.analyze(ast_objects[0])
        else:
            math_result = {"cost_expression": "0", "big_o": "O(1)"}

        response_data["hard_analysis"] = math_result
        response_data["status"] = "success"

    except Exception as e:
        logger.error(f"Error determinista: {e}")
        math_result = {
            "cost_expression": "Error de sintaxis/estructura",
            "big_o": "Indeterminado (Ver IA)",
            "error_details": str(e)
        }
        response_data["hard_analysis"] = math_result

    # 3. Consultor de Estrategia
    logger.info("3. Consultando IA...")
    strategy_report = explain_strategy(clean_code, math_result)
    response_data["soft_analysis"] = strategy_report

    return response_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)