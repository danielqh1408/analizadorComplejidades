from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.external.normalizer import normalize_code, explain_strategy
from src.modules.parser import PseudocodeParser
from src.modules.analyzer import ComplexityAnalyzer
from src.modules.patterns import LocalPatternMatcher
import uvicorn
import logging
import os
from dotenv import load_dotenv
import socket

#Este archivo crea una API con FastAPI que recibe código, lo normaliza, lo analiza matemáticamente y lo interpreta con IA.
#Es el centro de control del proyecto y nos da lugar a que se puede realizar todos los demas procesos
#De analisis de nuestro codigo.

# Carga .env y configura log básico
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Orchestrator")

#se crea la app
app = FastAPI(title="Analizador de Complejidad Híbrido")

class CodeRequest(BaseModel):
    code: str

def check_internet():
    #Verifica si hay conexión para llamar al LLM
    try:
        # Intenta conectar al DNS de Google
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

#Aqui es donde se realiza todo el analisis completo de nuestro proyecto
#Verifica si hay conexion, hace el proceso de normalizacion de la entrada de texto
#realiza el parsing y usa la IA para hacer las comprobaciones o ayudas necesarias para nuestro
#motor determinista
@app.post("/analyze")
async def analyze_algorithm(request: CodeRequest):
    response_data = {
        "status": "processing",
        "mode": "online",
        "input_analysis": {},
        "hard_analysis": {},
        "pattern_analysis": {},
        "soft_analysis": {},
        "warnings": [],
        "ast_debug": None
    }

    has_internet = check_internet()
    response_data["mode"] = "online" if has_internet else "offline"

    if not has_internet:
        response_data["warnings"].append("Modo Offline: Sin acceso a LLM. Funcionalidad reducida.")

    # 1. Normalización
    logger.info("1. Normalizando entrada...")
    clean_code = ""

    try:
        parser = PseudocodeParser()
        ast = parser.parse_text(request.code)
        clean_code = request.code # El código ya era válido
        logger.info("Código válido recibido directamente.")
    except Exception as e:
        # Falló parser directo. Necesitamos normalizar.
        if has_internet:
            logger.info("Código sucio. Usando LLM para normalizar...")
            clean_code = normalize_code(request.code)
            if "Error" in clean_code:
                raise HTTPException(status_code=400, detail="El LLM no pudo normalizar el código.")
        else:
            # SIN INTERNET y CÓDIGO SUCIO -> Error fatal
            return {
                "status": "error",
                "error": "Modo Offline: El código ingresado no cumple la gramática estricta y no se puede acceder a la IA para corregirlo. Por favor ingrese Pseudocódigo Pascal válido.",
                "mode": "offline"
            }

    response_data["input_analysis"]["final_code"] = clean_code

    # 2. Parsing y Análisis
    logger.info("2. Parseando y analizando...")
    try:
        parser = PseudocodeParser()
        ast = parser.parse_text(clean_code)

        response_data["ast_debug"] = [node.to_dict() for node in ast]
        
        analyzer = ComplexityAnalyzer()
        # Ahora obtenemos best, worst, average y line_costs
        math_results = analyzer.analyze(ast) 
        response_data["hard_analysis"] = math_results
        
    except Exception as e:
        response_data["hard_analysis"] = {"error": str(e)}
        response_data["warnings"].append("Error en el motor matemático.")

    # 3. Reconocimiento de Patrones (Local Primero)
    logger.info("3. Reconocimiento de Patrones...")
    local_pattern = LocalPatternMatcher.identify(clean_code)
    
    if local_pattern["pattern_found"]:
        response_data["pattern_analysis"] = local_pattern
    else:
        response_data["pattern_analysis"] = {"source": "Not found locally"}
        # Si no está local y no hay internet, nos quedamos así.
        if not has_internet:
             response_data["pattern_analysis"]["message"] = "Patrón no reconocido localmente y sin conexión a IA."

    # 4. Consultor de Estrategia
    logger.info("4. Consultando IA...")
    if has_internet:
        # Solo llamamos a la IA si hay internet
        # Le pasamos lo que encontró el motor local para que lo confirme o corrija
        context = {
            "math": response_data["hard_analysis"],
            "local_pattern": response_data["pattern_analysis"]
        }
        ai_report = explain_strategy(clean_code, context)
        response_data["soft_analysis"] = ai_report
    else:
        response_data["soft_analysis"] = {
            "strategy": "No disponible (Offline)",
            "explanation": "El análisis semántico requiere conexión a internet.",
            "validation": "Confíe en el cálculo del Motor Determinista."
        }

    response_data["status"] = "success"
    return response_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)