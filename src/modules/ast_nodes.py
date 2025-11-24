from dataclasses import dataclass
from typing import List, Optional, Any

# --- Interfaz del Visitante ---
class ASTVisitor:
    def visit(self, node: 'ASTNode'):
        """Despacha la llamada al método visit_NombreClase correspondiente."""
        method_name = f'visit_{type(node).__name__}'
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node: 'ASTNode'):
        raise NotImplementedError(f"No visit_{type(node).__name__} method defined")

# --- Nodos Base ---
@dataclass
class ASTNode:
    def accept(self, visitor: ASTVisitor):
        return visitor.visit(self)
    
    def to_dict(self) -> dict:
        """Serializa el nodo a un diccionario para enviarlo al frontend (JSON)."""
        node_type = type(self).__name__
        data = {"type": node_type}
        for key, value in self.__dict__.items():
            if isinstance(value, ASTNode):
                data[key] = value.to_dict()
            elif isinstance(value, list):
                data[key] = [item.to_dict() if isinstance(item, ASTNode) else str(item) for item in value]
            else:
                data[key] = str(value)
        return data

@dataclass
class Expression(ASTNode): pass
@dataclass
class Statement(ASTNode): pass

# --- Nodos de Expresión ---
@dataclass
class VarNode(Expression):
    name: str

@dataclass
class ConstNode(Expression):
    value: Any

@dataclass
class BinOpNode(Expression):
    left: Expression
    op: str
    right: Expression

@dataclass
class UnaryOpNode(Expression):
    op: str
    operand: Expression

# --- Nodos de Sentencias ---
@dataclass
class SequenceNode(Statement):
    statements: List[Statement]

@dataclass
class AssignNode(Statement):
    target: VarNode
    value: Expression

@dataclass
class ForLoopNode(Statement):
    variable: VarNode
    start: Expression
    end: Expression
    body: SequenceNode

@dataclass
class WhileLoopNode(Statement):
    condition: Expression
    body: SequenceNode

@dataclass
class IfNode(Statement):
    condition: Expression
    then_branch: SequenceNode
    else_branch: Optional[SequenceNode]

@dataclass
class CallNode(Statement):
    func_name: str
    args: List[Expression]

@dataclass
class FunctionNode(ASTNode):
    name: str
    params: List[VarNode]
    body: SequenceNode