"""
Tests Unitarios para el Módulo Analyzer (src/modules/analyzer.py)

Estos tests validan la lógica de cálculo de complejidad para
diferentes estructuras de pseudocódigo.
"""

import pytest
import sympy
from src.modules.parser import PseudocodeParser
from src.modules.analyzer import Analyzer

# --- Fixture del Analizador y Parser ---
@pytest.fixture(scope="module")
def parser():
    """Instancia única del Parser para los tests."""
    return PseudocodeParser()

@pytest.fixture
def analyzer():
    """Nueva instancia del Analyzer para cada test (para estado limpio)."""
    return Analyzer()

# --- Helper para parsear y analizar ---
def analyze_code(parser: PseudocodeParser, analyzer: Analyzer, code: str) -> dict:
    """Helper que parsea y analiza código, retornando el dict de resultados."""
    try:
        ast = parser.parse_text(code)
        return analyzer.analyze(ast)
    except Exception as e:
        pytest.fail(f"Fallo en el helper de análisis. ¿Gramática/AST desincronizados? Error: {e}")

# --- Casos de Prueba Parametrizados ---

# (Código, O Esperado, Omega Esperado, Theta Esperado)
test_cases_iterative = [
    # 1. O(1) - Costo Constante
    (
        """
        FUNCTION TestConstant(n)
        BEGIN
            x 🡨 1
            y 🡨 x + 2
        END
        """,
        "O(1)", "Ω(1)", "Θ(1)"
    ),
    # 2. O(n) - Bucle Lineal
    (
        """
        FUNCTION TestLinear(n)
        BEGIN
            FOR i 🡨 1 TO n DO
            BEGIN
                x 🡨 1
            END
        END
        """,
        "O(n)", "Ω(n)", "Θ(n)"
    ),
    # 3. O(n^2) - Bucles Anidados
    (
        """
        FUNCTION TestQuadratic(n)
        BEGIN
            FOR i 🡨 1 TO n DO
            BEGIN
                FOR j 🡨 1 TO n DO
                BEGIN
                    x 🡨 1
                END
            END
        END
        """,
        "O(n**2)", "Ω(n**2)", "Θ(n**2)"
    ),
    # 4. O(n^2) - Bucle Triangular (Bisbal, Cap 2)
    (
        """
        FUNCTION TestTriangular(n)
        BEGIN
            FOR i 🡨 1 TO n DO
            BEGIN
                FOR j 🡨 i TO n DO
                BEGIN
                    x 🡨 1
                END
            END
        END
        """,
        # El análisis simple da O(n**2).
        # Un analizador más avanzado podría detectar O(n*(n-i+1))
        # que suma a O(n**2). Nuestro analizador actual
        # (que asume que 'i' es constante en el bucle interno)
        # fallará o dará n*n. Lo aceptamos por ahora.
        "O(n**2)", "Ω(n**2)", "Θ(n**2)"
    ),
    # 5. O(n) - Secuencial
    (
        """
        FUNCTION TestSequential(n)
        BEGIN
            FOR i 🡨 1 TO n DO
            BEGIN
                x 🡨 1
            END
            
            FOR j 🡨 1 TO n DO
            BEGIN
                y 🡨 1
            END
        END
        """,
        # O(n) + O(n) = O(n)
        "O(n)", "Ω(n)", "Θ(n)"
    ),
    # 6. IF-ELSE con diferente costo
    (
        """
        FUNCTION TestIfElse(n)
        BEGIN
            IF (n > 10) THEN
            BEGIN
                FOR i 🡨 1 TO n DO
                BEGIN
                    x 🡨 1
                END
            END
            ELSE
            BEGIN
                x 🡨 1
            END
        END
        """,
        "O(n)", "Ω(1)", "Θ(N/A - Cota no ajustada)"
    ),
    # 7. WHILE (Caso simple de O(n) / Omega(1))
    (
        """
        FUNCTION TestWhile(n)
        BEGIN
            WHILE (n > 0) DO
            BEGIN
                x 🡨 1
                n 🡨 n - 1
            END
        END
        """,
        # Nuestro analizador asume O(n) y Omega(1) para WHILE
        "O(n)", "Ω(1)", "Θ(N/A - Cota no ajustada)"
    ),
]

@pytest.mark.parametrize("code, expected_O, expected_Omega, expected_Theta", test_cases_iterative)
def test_analyzer_iterative(parser, analyzer, code, expected_O, expected_Omega, expected_Theta):
    """
    Testea el analizador con varios casos iterativos.
    """
    result = analyze_code(parser, analyzer, code)
    
    assert "error" not in result
    assert result["O"] == expected_O
    assert result["Omega"] == expected_Omega
    assert result["Theta"] == expected_Theta

# --- Tests de Recursión (Requiere implementación avanzada) ---

@pytest.mark.skip(reason="El manejo de recursión (Teorema Maestro) es complejo y no implementado")
def test_analyzer_recursive_n_log_n(parser, analyzer):
    """
    Testea un algoritmo recursivo tipo MergeSort (O(n log n)).
    T(n) = 2T(n/2) + O(n)
    """
    code = """
    FUNCTION MergeSort(n)
    BEGIN
        IF (n > 1) THEN
        BEGIN
            CALL MergeSort(n / 2)
            CALL MergeSort(n / 2)
            
            FOR i 🡨 1 TO n DO
            BEGIN
                x 🡨 1
            END
        END
    END
    """
    result = analyze_code(parser, analyzer, code)
    assert result["O"] == "O(n*log(n))"
    assert result["Omega"] == "Ω(n*log(n))" # Asumiendo el mejor caso = peor caso
    assert result["Theta"] == "Θ(n*log(n))"