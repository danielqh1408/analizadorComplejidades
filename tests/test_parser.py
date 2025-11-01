"""
Tests Unitarios para el Módulo Parser (src/modules/parser.py)
"""

import pytest
from src.modules.parser import PseudocodeParser
from src.modules.ast_nodes import *

# --- Fixture del Parser ---
@pytest.fixture(scope="module")
def parser():
    """Retorna una instancia del parser para todos los tests."""
    try:
        return PseudocodeParser()
    except Exception as e:
        pytest.fail(f"Fallo al inicializar el PseudocodeParser. ¿Gramática corrupta? Error: {e}")

# --- Tests de Casos Válidos ---

def test_parse_simple_for(parser):
    """Prueba el parseo de un bucle FOR simple."""
    code = """
    FUNCTION TestSimpleFor(n)
    BEGIN
        FOR i 🡨 1 TO n DO
        BEGIN
            x 🡨 1
        END
    END
    """
    ast = parser.parse_text(code)
    
    assert isinstance(ast, list)
    assert len(ast) == 1
    func = ast[0]
    assert isinstance(func, FunctionNode)
    assert func.name == "TestSimpleFor"
    
    body = func.body
    assert isinstance(body, SequenceNode)
    assert len(body.statements) == 1
    
    for_loop = body.statements[0]
    assert isinstance(for_loop, ForLoopNode)
    assert for_loop.variable.name == "i"
    assert isinstance(for_loop.start, ConstNode)
    assert isinstance(for_loop.end, VarNode)
    
    for_body = for_loop.body
    assert isinstance(for_body, SequenceNode)
    assert isinstance(for_body.statements[0], AssignNode)

def test_parse_if_else(parser):
    """Prueba el parseo de una sentencia IF-THEN-ELSE."""
    code = """
    FUNCTION TestIfElse(n)
    BEGIN
        IF (n > 1) THEN
        BEGIN
            x 🡨 1
        END
        ELSE
        BEGIN
            x 🡨 2
        END
    END
    """
    ast = parser.parse_text(code)
    
    func = ast[0]
    if_node = func.body.statements[0]
    
    assert isinstance(if_node, IfNode)
    assert isinstance(if_node.condition, BinOpNode)
    assert if_node.condition.op == ">"
    assert isinstance(if_node.then_branch, SequenceNode)
    assert isinstance(if_node.else_branch, SequenceNode)
    assert if_node.else_branch.statements[0].value.value == 2

def test_parse_if_no_else(parser):
    """Prueba el parseo de una sentencia IF-THEN sin ELSE."""
    code = """
    FUNCTION TestIfNoElse(n)
    BEGIN
        IF (n = 1) THEN
        BEGIN
            x 🡨 1
        END
    END
    """
    ast = parser.parse_text(code)
    if_node = ast[0].body.statements[0]
    
    assert isinstance(if_node, IfNode)
    assert if_node.else_branch is None

def test_parse_nested_loops(parser):
    """Prueba el parseo de bucles anidados."""
    code = """
    FUNCTION TestNested(n)
    BEGIN
        FOR i 🡨 1 TO n DO
        BEGIN
            FOR j 🡨 1 TO n DO
            BEGIN
                x 🡨 1
            END
        END
    END
    """
    ast = parser.parse_text(code)
    outer_loop = ast[0].body.statements[0]
    assert isinstance(outer_loop, ForLoopNode)
    
    inner_loop = outer_loop.body.statements[0]
    assert isinstance(inner_loop, ForLoopNode)
    assert inner_loop.variable.name == "j"

# --- Tests de Casos Inválidos (Errores de Sintaxis) ---

@pytest.mark.parametrize("bad_code", [
    # FOR sin DO
    "FUNCTION TestBad(n) BEGIN FOR i 🡨 1 TO n x 🡨 1 END END",
    # IF sin THEN
    "FUNCTION TestBad(n) BEGIN IF (n > 1) x 🡨 1 END END",
    # BEGIN sin END
    "FUNCTION TestBad(n) BEGIN x 🡨 1",
    # Asignación inválida
    "FUNCTION TestBad(n) BEGIN 1 🡨 x END END",
])
def test_parse_syntax_errors(parser, bad_code):
    """
    Prueba que el parser lance SyntaxError en estructuras mal formadas.
    (Lark lanzará un 'UnexpectedToken' o similar, que capturamos como SyntaxError).
    """
    with pytest.raises(SyntaxError):
        parser.parse_text(bad_code)