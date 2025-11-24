import os
import google.generativeai as genai
from dotenv import load_dotenv
# Si no tienes un logger configurado aún, usa print o logging básico temporalmente
# from src.services.logger import get_logger 
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY no encontrada en el archivo .env")
else:
    genai.configure(api_key=api_key)

def normalize_code(user_input: str) -> str:
    """
    Toma código sucio/natural y lo convierte en Pascal estricto para Lark.
    """
    if not api_key:
        return "Error: API Key no configurada."

    model = genai.GenerativeModel('gemini-3-pro-preview') 
    
    # GRAMÁTICA EXACTA DE TU PARSER (Simplificada para el prompt)
    # Esta gramática coincide con lo que definimos para Lark
    grammar_rules = """
    TU OBJETIVO: Convertir la entrada en código PASCAL SIMPLIFICADO que cumpla ESTRICTAMENTE estas reglas.
    
    ESTRUCTURA OBLIGATORIA:
    1. Todo programa debe estar dentro de una función:
       FUNCTION NombreAlgoritmo(param1, param2)
       BEGIN
          ... instrucciones ...
       END
    
    2. Asignación: Usa SIEMPRE "<-" (ej: x <- 0). NUNCA uses "=" ni ":=".
    
    3. Bucles FOR:
       FOR i <- 0 TO n DO
       BEGIN
           ...
       END
    
    4. Bucles WHILE:
       WHILE (condicion) DO
       BEGIN
           ...
       END
       
    5. Condicional IF:
       IF (x > 0) THEN
       BEGIN
           ...
       END
       ELSE
       BEGIN
           ...
       END

    REGLAS DE ORO:
    - Siempre encierra el cuerpo de los bucles e if en BEGIN ... END.
    - No uses 'return', el análisis es estático.
    - Solo genera el código. Sin explicaciones. Sin markdown (```).
    """
    
    prompt = f"""
    {grammar_rules}
    
    ENTRADA DEL USUARIO:
    {user_input}
    
    SALIDA NORMALIZADA (Solo código):
    """
    
    try:
        response = model.generate_content(prompt)
        # Limpieza básica por si el LLM pone markdown a pesar de la instrucción
        code = response.text.replace("```pascal", "").replace("```", "").strip()
        return code
    except Exception as e:
        logger.error(f"Error normalizando código con Gemini: {e}")
        return f"// Error en normalización: {str(e)}"

def explain_strategy(clean_code: str, math_result: dict) -> dict:
    """
    Paso 4: El LLM actúa como consultor senior para clasificar la estrategia
    y validar el hallazgo matemático.
    """
    if not api_key:
        return {"error": "Sin API Key"}

    try:
        model = genai.GenerativeModel('gemini-3-pro-preview')
        
        prompt = f"""
        ACTÚA COMO UN PROFESOR EXPERTO EN ANÁLISIS DE ALGORITMOS.
        
        Analiza el siguiente código (Pascal Simplificado):
        --------------------------------------------------
        {clean_code}
        --------------------------------------------------
        
        Datos del Análisis Matemático Estático:
        - Complejidad: {math_result.get('big_o', 'Desconocida')}
        - Recurrencia detectada: {math_result.get('recurrence_equation', 'Ninguna')}

        TU TAREA:
        Genera un JSON válido con la siguiente estructura exacta.
        
        REGLAS PARA EL CAMPO 'strategy':
        Debes clasificar el algoritmo EXCLUSIVAMENTE en una de estas categorías (elige la que mejor encaje):
        1. "Divide y Vencerás" (Si hay recursión partitiva T(n/b))
        2. "Programación Dinámica" (Si hay tablas/memoización)
        3. "Voraz (Greedy)" (Si toma óptimos locales)
        4. "Backtracking" (Si explora y retrocede)
        5. "Ramificación y Poda (Branch & Bound)"
        6. "Heurístico / Aproximado"
        7. "Fuerza Bruta / Iterativo Simple" (Para bucles anidados básicos)

        FORMATO DE RESPUESTA (JSON puro, sin markdown):
        {{
            "strategy": "Escribe aquí EXACTAMENTE una de las categorías de la lista anterior",
            "explanation": "Explicación técnica breve (máx 2 frases) justificando la clasificación.",
            "complexity_validation": "Confirma si el cálculo matemático ({math_result.get('big_o')}) es correcto o si hay matices (ej: caso promedio vs peor caso).",
            "pattern_identified": "Nombre del patrón o algoritmo clásico (ej: MergeSort, Mochila, Viajero, Busqueda Binaria, etc.)"
        }}
        """
        
        response = model.generate_content(prompt)
        # Limpieza agresiva para asegurar JSON válido
        text = response.text.replace("```json", "").replace("```", "").strip()
        import json
        return json.loads(text)
        
    except Exception as e:
        logger.error(f"Error en explicación de estrategia: {e}")
        # Fallback para que el front no rompa
        return {
            "strategy": "Desconocida", 
            "explanation": f"Error procesando respuesta IA: {str(e)}",
            "complexity_validation": "N/A",
            "name_guess": "N/A"
        }

# Pequeña prueba unitaria si ejecutas el archivo directo
if __name__ == "__main__":
    test_input = "haz una funcion que sume dos numeros a y b"
    print(f"Input: {test_input}")
    print("Output:")
    print(normalize_code(test_input))