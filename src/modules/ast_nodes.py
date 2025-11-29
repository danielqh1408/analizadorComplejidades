#Aqui se contruye y como se constituye el arbol mediante los nodos
#Esto proporcionado por el JSON del AST, el entiende el codigo y crea los nodos para el arbol

from dataclasses import dataclass, field
from typing import List, Optional, Any

#Interfaz del Visitante

# Esta clase sirve para recorrer todo el programa paso a paso.
# Identifica qué tipo de instrucción es cada parte y la procesa correctamente.
class ASTVisitor:
    def visit(self, node: 'ASTNode'):
        #Despacha la llamada al método visit_NombreClase correspondiente.
        method_name = f'visit_{type(node).__name__}'
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node: 'ASTNode'):
        raise NotImplementedError(f"No visit_{type(node).__name__} method defined")

#Nodos Base

# Esta es la clase base de todos los nodos del árbol del programa
# Representa cualquier elemento del código (variables, condiciones, bucles, etc.).
@dataclass
class ASTNode:
    line: Optional[int] = field(default=None, init=False)
    def accept(self, visitor: ASTVisitor):
        return visitor.visit(self)
    
    def to_dict(self) -> dict:
        node_type = type(self).__name__
        data = {"type": node_type}
        if self.line is not None:
            data["line"] = self.line
            
        for key, value in self.__dict__.items():
            if key == "line": continue
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

# Nodos de Expresión

#Maneja todo los tipos de expresiones
#Como variables, constantes, strings, etc. 
@dataclass
class VarNode(Expression):
    name: str

@dataclass
class ConstNode(Expression):
    value: Any

@dataclass
class StringNode(Expression):
    value: str

@dataclass
class BinOpNode(Expression):
    left: Expression
    op: str
    right: Expression

@dataclass
class UnaryOpNode(Expression):
    op: str
    operand: Expression

#Nodos de Sentencias

#Representa los bloques de instrucciones
@dataclass
class SequenceNode(Statement):
    statements: List[Statement]

#Representa las asignaciones
@dataclass
class AssignNode(Statement):
    target: VarNode
    value: Expression

#Estos tres representan los bucles y el condicional if 
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

#Representa el llamado a una función
@dataclass
class CallNode(Statement):
    func_name: str
    args: List[Expression]

#Representa una funcion completa
@dataclass
class FunctionNode(ASTNode):
    name: str
    params: List[VarNode]
    body: SequenceNode