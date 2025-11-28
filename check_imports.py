# Este archivo se usa únicamente para comprobar que las librerías necesarias estén instaladas
# correctamente y que el sistema pueda trabajar con los servicios de Inteligencia Artificial
# sin problemas antes de ejecutar el programa principal.

try:
    from google.api_core.exceptions import ResourceExhausted
    print("ResourceExhausted imported successfully")
except ImportError:
    print("Could not import ResourceExhausted")

import google.generativeai as genai
print(f"genai version: {genai.__version__}")
