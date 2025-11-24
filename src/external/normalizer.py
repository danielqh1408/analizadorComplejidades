import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import time
import random
import json

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY no encontrada en el archivo .env")
else:
    genai.configure(api_key=api_key)

def retry_api_call(func, *args, **kwargs):
    """
    Intenta llamar a la API hasta 3 veces con espera exponencial si falla por cuota.
    """
    max_retries = 3
    base_delay = 2  # Segundos

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e)
            # Detectar error 429 o ResourceExhausted
            if "429" in error_str or "ResourceExhausted" in error_str:
                if attempt < max_retries - 1:
                    # Exponential backoff + jitter
                    sleep_time = (base_delay * (30 ** attempt)) + random.uniform(0, 1)
                    logger.warning(f"Rate limit alcanzado. Reintentando en {sleep_time:.2f}s... (Intento {attempt + 1}/{max_retries})")
                    time.sleep(sleep_time)
                else:
                    logger.error("Se agotaron los reintentos por Rate Limit.")
                    raise e
            else:
                # Si es otro error, fallar inmediatamente
                raise e

def normalize_code(user_input: str) -> str:
    """
    Toma código sucio/natural y lo convierte en Pascal estricto para Lark.
    """
    if not api_key:
        return "Error: API Key no configurada."

    model = genai.GenerativeModel('gemini-2.5-flash') 
    
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
        response = retry_api_call(model.generate_content, prompt)
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
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        ACTÚA COMO UN PROFESOR EXPERTO EN ANÁLISIS DE ALGORITMOS (Experto en Cormen y Bisbal Riera).
        
        Analiza el siguiente código (Pascal Simplificado):
        --------------------------------------------------
        {clean_code}
        --------------------------------------------------

        RESULTADOS DEL MOTOR DETERMINISTA:
        - Ecuación de Coste: {math_result.get('cost_expression', 'No disponible')}
        - Complejidad Calculada: {math_result.get('big_o', 'Indeterminada')}
        - Recursivo: {math_result.get('is_recursive', False)}
        - Ecuación de Recurrencia: {math_result.get('recurrence_equation', 'Ninguna')}

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
        8. "MinMax / Adversarial" (Para algoritmos de juegos)

        SI EL ALGORITMO ES RECURSIVO:
        Genera una breve representación del "Árbol de Recurrencia" en texto ASCII o explica los niveles:
        - Nivel 0: Coste k
        - Nivel 1: Coste k/2...
        Esto es para justificar el cálculo del Teorema Maestro.

        FORMATO DE RESPUESTA (JSON puro, sin markdown):
        {{
            "strategy": "Escribe aquí EXACTAMENTE una de las categorías de la lista anterior",
            "explanation": "Explicación técnica breve (máx 2 frases) justificando la clasificación (SI ES ITERATIVO: Explica cómo la sumatoria de los bucles lleva a la complejidad (Método de Iteración).
            - SI ES RECURSIVO: Explica brevemente cómo se aplicaría el Árbol de Recurrencia o el Teorema Maestro para llegar al resultado.
            - SI ES VORAZ/DINÁMICO: Explica la subestructura óptima o la elección codiciosa.).",
            "complexity_validation": "Confirma si el cálculo matemático ({math_result.get('big_o')}) es correcto o si hay matices (ej: caso promedio vs peor caso).",
            "pattern_identified": "Nombre del patrón o algoritmo clásico (ej: MergeSort, Mochila, Viajero, Busqueda Binaria, etc.)",
            "method_used": "Indica qué método teórico justifica mejor la complejidad:
            - 'Método de Sumatorias/Iteración' (Para bucles)
            - 'Teorema Maestro' (Para T(n) = aT(n/b) + f(n))
            - 'Árbol de Recurrencia' (Para recursión irregular)
            - 'Método de Sustitución' (Para demostraciones complejas)."
        }}
        """
        
        response = retry_api_call(model.generate_content, prompt)
        # Limpieza agresiva para asegurar JSON válido
        text = response.text.replace("```json", "").replace("```", "").strip()
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