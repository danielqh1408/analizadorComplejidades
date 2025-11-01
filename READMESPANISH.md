# 🧩 Proyecto Analizador de Complejidades

**Versión:** 1.0.0  
**Lenguaje:** Python 3.11  
**Autor:** Daniel Quintero Hurtado - Jeronimo Garcia Parra
**Arquitectura:** Sistema Modular de 3 Capas (Frontend · Backend · Servicios Externos)

## 📘 Descripción General

El **Analizador de Complejidades** es un sistema modular diseñado para **analizar la complejidad algorítmica (O, Ω, Θ)** combinando dos enfoques:

1. **Análisis determinista**, basado en la construcción y recorrido de Árboles de Sintaxis Abstracta (AST) mediante reglas formales.  
2. **Asistencia con Inteligencia Artificial**, utilizando modelos LLM (como **Gemini** u **OpenAI**) para validación, traducción y explicación de algoritmos.

La arquitectura se fundamenta en principios de diseño de compiladores y análisis de algoritmos, tomando como base teórica los textos de **Cormen et al. (Introduction to Algorithms, 4ª edición)** y **Bisbal Riera (Manual de Algorítmica: Recursividad, Complejidad y Diseño de Algoritmos)**.

## ⚙️ Requisitos del Sistema

| Componente | Mínimo | Recomendado |
|-------------|---------|--------------|
| **Python** | 3.11 | 3.11+ |
| **CPU** | 4 núcleos | AMD Ryzen 7 7700X (8 núcleos / 16 hilos) |
| **GPU** | Opcional | NVIDIA RTX 4060 Ti (CUDA 12.x) |
| **RAM** | 8 GB | 32 GB DDR5 5200 MHz |
| **Almacenamiento** | 2 GB | SSD / NVMe |

## 🧱 Estructura del Proyecto

ANALIZADORCOMPLEJIDADES/
├─ Architecture/
│ ├─ Arquitectura.drawio
│ └─ ArquitecturaF.png
├─ data/
│ ├─ examples/info.txt
│ └─ tests/info.txt
├─ docs/
│ └─ architecture.md
├─ src/
│ ├─ external/
│ │ ├─ init.py
│ │ └─ llm_assistant.py
│ ├─ modules/
│ │ ├─ init.py
│ │ ├─ analyzer.py
│ │ ├─ ast_nodes.py
│ │ ├─ lexer.py
│ │ └─ parser.py
│ ├─ services/
│ │ ├─ init.py
│ │ ├─ file_io.py
│ │ ├─ logger.py
│ │ └─ metrics.py
│ └─ main.py
├─ tests/
├─ .gitignore
├─ config.ini
├─ README.md
└─ requirements.txt

## 🧩 Guía de Instalación

### 1️⃣ Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/AnalizadorComplejidades.git
cd AnalizadorComplejidades
2️⃣ Crear un Entorno Virtual
Se recomienda trabajar dentro de un entorno virtual para evitar conflictos:

python -m venv venv

Activación:

Windows:

venv\Scripts\activate

Linux/Mac:

source venv/bin/activate

3️⃣ Instalar Dependencias
Todas las librerías están fijadas para Python 3.11:

pip install -r requirements.txt

Si cuentas con una GPU NVIDIA (CUDA 12.x):

pip install cupy-cuda12x

🧠 Dependencias Principales
Librería	Función
NumPy	Operaciones numéricas base
Numba	Compilación JIT y optimización CPU/GPU
SymPy	Cálculo simbólico y resolución de recurrencias
Cython	Optimización de bajo nivel
CuPy	Computación acelerada por GPU
Joblib / Multiprocess	Ejecución paralela
FastAPI + Uvicorn	Servidor y API backend
Lark-parser	Análisis léxico y sintáctico (gramática)
Graphviz	Visualización de árboles AST
Rich	Formato de salida y depuración en consola

🚀 Ejecución del Proyecto
Opción A — Ejecución del Núcleo del Analizador
bash
Copiar código
python src/main.py
Opción B — Modo API (Backend con FastAPI)
Iniciar el servidor:

uvicorn src.main:app --reload

Luego acceder a:

http://127.0.0.1:8000/docs

🧮 Módulos Principales
Módulo	Descripción
lexer.py	Convierte pseudocódigo en una secuencia de tokens
parser.py	Construye y valida el Árbol de Sintaxis Abstracta (AST)
ast_nodes.py	Define las estructuras de datos del AST
analyzer.py	Aplica reglas deterministas para obtener O, Ω y Θ
llm_assistant.py	Interactúa con APIs LLM (Gemini / OpenAI)
file_io.py	Gestión de lectura y escritura de archivos
metrics.py	Registro de métricas (tiempo, tokens, latencia)
logger.py	Registro de eventos y trazas del sistema

⚡ Optimización de Rendimiento
Ejecución Paralela: Uso de Numba, Joblib o Multiprocess para aprovechar los 16 hilos del Ryzen 7 7700X.

Aceleración GPU: Posibilidad de usar CuPy o Numba CUDA para operaciones numéricas pesadas.

Optimización de Memoria: Estructuras vectorizadas y operaciones in-place para aprovechar la DDR5 de alta frecuencia.

🧰 Pruebas
Las pruebas unitarias y de integración se ubican en:

/tests
Ejecutar todas las pruebas:

pytest -v

📖 Referencias
Introduction to Algorithms, Cormen et al., 4ª Edición.

Manual de Algorítmica: Recursividad, Complejidad y Diseño de Algoritmos, Bisbal Riera.

Documentación interna:

Proyecto_Analizador_Complejidades.docx

Proyecto_Gramatica.docx

🧑‍💻 Nota del Autor
Este proyecto combina análisis algorítmico formal con razonamiento asistido por IA, integrando teoría de compiladores con procesamiento en lenguaje natural.
El código está diseñado para ser modular, extensible y eficiente, aprovechando al máximo el hardware disponible.

📜 Licencia
Distribuido bajo la Licencia MIT.
Se permite su uso, modificación y distribución con la debida atribución.