try:
    from google.api_core.exceptions import ResourceExhausted
    print("ResourceExhausted imported successfully")
except ImportError:
    print("Could not import ResourceExhausted")

import google.generativeai as genai
print(f"genai version: {genai.__version__}")
