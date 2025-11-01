"""
Definición de Nodos del Árbol de Sintaxis Abstracta (AST)

Este módulo define las estructuras de datos (dataclasses) para cada nodo
que compone el AST. Implementa el patrón de diseño Visitor
(con los métodos 'accept') para permitir que los 'visitantes'
(como el 'Analyzer') recorren la estructura.
"""

from dataclasses import dataclass
from typing import List, Optional, Union, Any

# --- Interfaz del Visitante ---

class ASTVisitor:
    """
    Clase base para el patrón Visitor.
    Define un método 'visit' que despacha a métodos específicos
    del tipo de nodo (ej. 'visit_ForLoopNode').
    """
    def visit(self, node: 'ASTNode'):
        """Método de despacho del Visitante."""
        method_name = f'visit_{type(node).__name__}'
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node: 'ASTNode'):
        """Método de fallback si no se encuentra un 'visit_NodeType'."""
        raise NotImplementedError(f"No visit_{type(node).__name__} method defined")

# --- Nodos Base ---

@dataclass
class ASTNode:
    """Nodo base para todos los elementos del AST."""
    def accept(self, visitor: ASTVisitor):
        """Acepta un visitante."""
        return visitor.visit(self)

@dataclass
class Expression(ASTNode):
    """Nodo base para todas las expresiones."""
    pass

@dataclass
class Statement(ASTNode):
    """Nodo base para todas las sentencias."""
    pass

# --- Nodos de Expresión (Valores) ---

@dataclass
class VarNode(Expression):
    """Representa una variable (ej. 'n', 'i')."""
    name: str

@dataclass
class ConstNode(Expression):
    """Representa un valor constante (ej. 1, 100)."""
    value: Any # (generalmente int o float)

@dataclass
class BinOpNode(Expression):
    """Representa una operación binaria (ej. 'n / 2', 'i + 1')."""
    left: Expression
    op: str # (ej. '+', '-', '*', '/')
    right: Expression

# --- Nodos de Sentencias ---

@dataclass
class SequenceNode(Statement):
    """Representa un bloque de sentencias (ej. BEGIN...END)."""
    statements: List[Statement]

@dataclass
class AssignNode(Statement):
    """Representa una asignación (ej. 'x 🡨 1')."""
    target: VarNode
    value: Expression

@dataclass
class ForLoopNode(Statement):
    """Representa un bucle FOR."""
    variable: VarNode
    start: Expression
    end: Expression
    body: SequenceNode

@dataclass
class WhileLoopNode(Statement):
    """Representa un bucle WHILE."""
    condition: Expression
    body: SequenceNode

@dataclass
class IfNode(Statement):
    """Representa un condicional IF-THEN-ELSE."""
    condition: Expression
    then_branch: SequenceNode
    else_branch: Optional[SequenceNode] # None si no hay ELSE

@dataclass
class CallNode(Statement):
    """Representa una llamada a función (ej. 'CALL MyFunc(n)')."""
    func_name: str
    args: List[Expression]

@dataclass
class FunctionNode(ASTNode):
    """Representa una definición de función/algoritmo completo."""
    name: str
    params: List[VarNode]
    body: SequenceNode