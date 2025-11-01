# 🧠 Developer Documentation — Complexity Analyzer Project

**Project:** Analizador de Complejidades  
**Language:** Python 3.11  
**Version:** 1.0.0  
**Author:** Daniel Quintero Hurtado - Jeronimo Garcia Parra
**Audience:** Developers & Researchers extending backend logic or performance modules.

## 🧩 Objetivo del Documento

Este documento técnico está dirigido a los **desarrolladores** del proyecto.  
Su propósito es describir:

- Cómo extender y mantener los módulos principales.  
- Cómo ejecutar y medir el rendimiento (CPU / GPU).  
- Qué estándares de codificación y herramientas se utilizan.  
- Cómo aplicar optimización con **Numba**, **CuPy** y **Joblib**.  

## ⚙️ Entorno de Desarrollo Recomendado

| Componente | Requerido |
|-------------|-----------|
| **Python** | 3.11 |
| **IDE** | Visual Studio Code o PyCharm |
| **Linter** | flake8 / pylint |
| **Formateador** | black (PEP8 compliant) |
| **Testing** | pytest |
| **Documentación** | docstring estilo Google / reStructuredText |
| **Sistema Operativo** | Linux / Windows 11 (64-bit) |
| **GPU (opcional)** | NVIDIA RTX 4060 Ti, CUDA 12.x |
| **CPU** | AMD Ryzen 7 7700X (8 núcleos / 16 hilos) |

## 📁 Estructura Interna del Proyecto

src/
├─ external/ → Módulos de conexión con LLMs externos (Gemini / OpenAI)
├─ modules/ → Núcleo lógico (lexer, parser, AST, analyzer)
├─ services/ → Servicios de apoyo (logger, métricas, IO, orquestador)
├─ main.py → Punto de entrada principal
└─ tests/ → Pruebas unitarias e integración

## 🧱 Arquitectura Interna de Módulos

Cada módulo sigue un patrón estandarizado:

| Elemento | Convención |
|-----------|------------|
| **Clase Principal** | `PascalCase` (ej. `Lexer`, `Analyzer`) |
| **Funciones** | `snake_case` (ej. `analyze_token_stream()`) |
| **Variables** | `snake_case` |
| **Constantes** | `UPPER_CASE` |
| **Comentarios** | En inglés, concisos y explicativos |
| **Docstrings** | Google Style (para compatibilidad con autodoc) |

Ejemplo:
```python
def analyze_loop_complexity(loop_node: ASTNode) -> Complexity:
    """
    Analyzes the computational complexity of a loop construct.

    Args:
        loop_node (ASTNode): Node representing the loop in the AST.

    Returns:
        Complexity: Object containing O, Ω, and Θ results.

    Based on:
        Cormen (Ch. 2–4) and Bisbal (Cap. 2.2.3)
    """

🚀 Ejecución y Desarrollo
1️⃣ Ejecutar en modo desarrollo
python src/main.py --dev

2️⃣ Lanzar el servidor API (FastAPI)

uvicorn src.main:app --reload
Interfaz interactiva:

http://127.0.0.1:8000/docs

3️⃣ Ejecutar todas las pruebas
pytest -v

4️⃣ Ejecutar pruebas de rendimiento
python -m tests.performance_bench

⚡ Optimización y Paralelismo
🧮 1. Aceleración con Numba
Para funciones puramente numéricas o de conteo:

from numba import njit, prange

@njit(parallel=True, fastmath=True)
def count_operations(loop_range: int) -> int:
    total = 0
    for i in prange(loop_range):
        total += i * 2
    return total
Ventajas:

Compilación JIT a nivel de CPU nativo (LLVM).

Uso de SIMD y vectorización automática.

Escala con múltiples núcleos (paralelismo real).

🔥 2. Aceleración con CuPy (GPU)
Para cálculos intensivos:

import cupy as cp

def gpu_matrix_sum(n: int) -> float:
    A = cp.arange(n**2, dtype=cp.float32).reshape(n, n)
    B = cp.ones((n, n), dtype=cp.float32)
    return float(cp.sum(A * B))
Ventajas:

Computación paralela masiva en GPU.

API compatible con NumPy.

Ideal para simulaciones o recorridos de AST grandes.

⚙️ 3. Ejecución Paralela con Multiprocessing / Joblib
from joblib import Parallel, delayed

def analyze_case(case):
    return analyzer.evaluate(case)

results = Parallel(n_jobs=8)(delayed(analyze_case)(c) for c in cases)
Usa todos los núcleos del Ryzen 7 7700X con balance automático.

📊 Medición de Rendimiento
Usar módulo interno metrics.py
Ejemplo:

from src.services.metrics import MetricsLogger

metrics = MetricsLogger()
metrics.start_timer("Lexer")
tokens = lexer.tokenize(source_code)
metrics.end_timer("Lexer")
metrics.log("Lexer", len(tokens), "tokens processed")
Salida esperada:

[METRICS] Lexer: 12.45ms — 186 tokens processed
🧩 Flujo Interno del Sistema
Lexer: Tokeniza el pseudocódigo (lexical analysis).

Parser: Construye el Árbol de Sintaxis Abstracta (AST).

Analyzer: Aplica reglas de complejidad determinista.

LLM Assistant: Valida, explica o traduce según el contexto.

Orchestrator: Coordina tareas paralelas y consolida resultados.

🧠 Buenas Prácticas de Desarrollo
Evitar acoplamientos cruzados entre módulos (usar interfaces claras).

Comentar razonamientos complejos o fórmulas de análisis.

Validar entradas y salidas de cada componente.

Evitar dependencias circulares entre archivos.

Mantener la coherencia teórica con las referencias (Cormen y Bisbal).

🧩 Cómo Extender el Proyecto
Añadir una nueva regla de complejidad
Editar src/modules/analyzer.py.

Implementar la regla en una nueva función con docstring explicativo.

Registrar la regla en el mapa de análisis del AST.

Añadir pruebas unitarias bajo /tests.

Añadir soporte para nuevo tipo de bucle o estructura
Actualizar la gramática en Proyecto_Gramatica.docx.

Ajustar parser.py para reconocer la nueva estructura.

Agregar el comportamiento correspondiente en el AST Walker.

🧰 Herramientas Recomendadas
Line profiler: pip install line_profiler

Memory profiler: pip install memory_profiler

Benchmark CLI: pytest-benchmark

GPU monitor: nvidia-smi

🧩 Ejemplo de Flujo Completo (Lexer → Análisis)
python -m src.modules.lexer
python -m src.modules.parser
python -m src.modules.analyzer
Salida esperada:

[LEXER]  ✅ Tokens generated: 184
[PARSER] ✅ AST constructed: 32 nodes
[ANALYZER] 🧮 Complexity: O(n log n), Ω(n), Θ(n log n)

📖 Referencias Técnicas
Cormen, T. H. et al. Introduction to Algorithms, 4ª edición.

Bisbal Riera, J. Manual de Algorítmica: Recursividad, Complejidad y Diseño de Algoritmos.

Documentos internos del proyecto:

Proyecto_Analizador_Complejidades.docx

Proyecto_Gramatica.docx

Arquitectura: Architecture/ArquitecturaF.png

🧑‍💻 Contacto
Autores: Daniel Quintero Hurtado - Jeronimo Garcia Parra
Colaboraciones: se aceptan pull requests con documentación clara y pruebas incluidas.

📜 Licencia
Distribuido bajo la Licencia MIT.
Puedes usarlo, modificarlo y distribuirlo libremente, citando la fuente.