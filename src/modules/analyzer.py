"""
Motor de Análisis de Complejidad (AST Walker)

Este módulo implementa el Visitor que recorre el AST (generado por
'parser.py') y calcula la complejidad simbólica.

Utiliza 'sympy' para manejar expresiones matemáticas.
La lógica se basa en los principios de análisis de algoritmos de
Cormen (ej. Cap 2, Cap 4) y Bisbal (ej. Cap 2).
"""

import sympy
from sympy import Symbol, sympify, Max, Min, oo
from typing import Dict, Any, Optional

from src.modules.ast_nodes import *
from src.services.logger import get_logger
from src.services.metrics import metrics_logger

logger = get_logger(__name__)

# --- Clase de Resultado Simbólico ---
@dataclass
class ComplexityResult:
    """Almacena los costos simbólicos para los 3 casos."""
    # O (Peor Caso)
    O: sympy.Expr
    # Ω (Mejor Caso)
    Omega: sympy.Expr
    
    def __add__(self, other: 'ComplexityResult'):
        """Suma costos secuenciales."""
        return ComplexityResult(self.O + other.O, self.Omega + other.Omega)

    def __mul__(self, other: sympy.Expr):
        """Multiplica costos (para bucles)."""
        return ComplexityResult(self.O * other, self.Omega * other)
        
    @staticmethod
    def O_Omega_from_branches(cond_cost, then_cost, else_cost):
        """Calcula costos para ramas IF (Cormen/Bisbal)."""
        O = cond_cost.O + Max(then_cost.O, else_cost.O)
        Omega = cond_cost.Omega + Min(then_cost.Omega, else_cost.Omega)
        return ComplexityResult(O, Omega)

# --- Motor del Analizador (Visitor) ---

class Analyzer(ASTVisitor):
    """
    Implementa el AST Visitor para el análisis de complejidad.
    
    Recorre el AST y construye expresiones simbólicas en 'sympy'
    para el costo del peor caso (O) y mejor caso (Ω).
    """
    
    def __init__(self):
        # Símbolo principal para el análisis
        self.n = Symbol('n', integer=True, positive=True)
        # Símbolos para iteradores de bucles
        self.i = Symbol('i', integer=True)
        self.j = Symbol('j', integer=True)
        self.k = Symbol('k', integer=True)
        
        # Almacena los costos de las funciones (para recursión)
        self.function_costs: Dict[str, Any] = {}
        self.current_function: Optional[FunctionNode] = None

    def analyze(self, ast_nodes: List[FunctionNode]) -> Dict[str, Any]:
        """
        Punto de entrada principal. Analiza una lista de funciones
        y devuelve un diccionario de complejidades.
        """
        metrics_logger.start_timer("analysis_total")
        
        # 1. Analizar todas las funciones
        for func_node in ast_nodes:
            self.visit(func_node)
            
        # 2. Por ahora, devolvemos el análisis de la *primera* función
        # (asumiendo que es la principal)
        if not ast_nodes:
            return {"error": "No se encontraron funciones para analizar."}
            
        main_func_name = ast_nodes[0].name
        if main_func_name not in self.function_costs:
            return {"error": f"El análisis de la función principal '{main_func_name}' falló."}
            
        raw_result: ComplexityResult = self.function_costs[main_func_name]
        
        # 3. Simplificar y formatear la salida
        O_expr = self._get_dominant_term(raw_result.O)
        Omega_expr = self._get_dominant_term(raw_result.Omega)
        
        # Determinar Theta (Cormen, Cap 3.1)
        if O_expr == Omega_expr:
            Theta_expr = Omega_expr
        else:
            Theta_expr = None # No hay cota ajustada

        metrics_logger.end_timer("analysis_total")
        
        return {
            "O": f"O({O_expr})",
            "Omega": f"Ω({Omega_expr})",
            "Theta": f"Θ({Theta_expr})" if Theta_expr else f"Θ(N/A - Cota no ajustada)",
            "raw_O": str(raw_result.O.simplify()),
            "raw_Omega": str(raw_result.Omega.simplify())
        }
        
    def _get_dominant_term(self, expr: sympy.Expr) -> sympy.Expr:
        """
        Extrae el término dominante de una expresión de sympy.
        (Ej. n**2 + n + 1 -> n**2)
        """
        try:
            # Simplificar primero
            simplified = expr.simplify()

            # Si la expresión no depende de 'n' (constante), su cota asintótica es O(1)
            if not simplified.has(self.n) or simplified.is_constant():
                return sympify(1)

            # leadterm() es la forma estándar para expresiones con 'n'
            dominant = sympy.O(simplified, (self.n, sympy.oo)).args[0]

            # Si el término es solo un coeficiente, devolver 'n'
            if dominant.is_Number:
                 return self.n
            
            return dominant
        
        except (TypeError, AttributeError, NotImplementedError):
            # Fallback para expresiones complejas (ej. log(n))
            simplified = expr.simplify()
            if not simplified.has(self.n) or simplified.is_constant():
                return sympify(1)
            return simplified.as_expr().subs(self.i, self.n).subs(self.j, self.n).subs(self.k, self.n)

    def _resolve_expr(self, expr_node: Expression) -> sympy.Expr:
        """Convierte un nodo de expresión del AST a un símbolo de sympy."""
        if isinstance(expr_node, VarNode):
            current_param_names = [p.name for p in self.current_function.params]

            if expr_node.name in current_param_names:
                return self.n
            # Asumimos otras variables como constantes de tiempo 1
            return Symbol(expr_node.name, integer=True)
        elif isinstance(expr_node, ConstNode):
            return sympify(expr_node.value)
        elif isinstance(expr_node, BinOpNode):
            left = self._resolve_expr(expr_node.left)
            right = self._resolve_expr(expr_node.right)
            # Evaluar la operación
            if expr_node.op == '+': return left + right
            if expr_node.op == '-': return left - right
            if expr_node.op == '*': return left * right
            if expr_node.op == '/': return left / right
        return sympify(1) # Costo por defecto para expresiones

    # --- Métodos Visitantes (Implementación del AST Walker) ---

    def visit_FunctionNode(self, node: FunctionNode):
        logger.info(f"Analizando función: {node.name}")
        self.current_function = node
        
        # Analizar el cuerpo
        body_cost = node.body.accept(self)
        
        # TODO: Detectar recursión aquí
        # (Esta es la parte más compleja, omitida por brevedad
        # y se enfoca en el análisis iterativo primero)
        
        self.function_costs[node.name] = body_cost
        self.current_function = None
        return body_cost

    def visit_SequenceNode(self, node: SequenceNode):
        """Suma los costos de las sentencias secuenciales."""
        cost = ComplexityResult(sympify(0), sympify(0))
        for stmt in node.statements:
            cost += stmt.accept(self)
        return cost

    def visit_AssignNode(self, node: AssignNode):
        """Costo constante (O(1)) para asignación."""
        expr_cost = node.value.accept(self)
        return ComplexityResult(sympify(1) + expr_cost.O, sympify(1) + expr_cost.Omega)

    def visit_ForLoopNode(self, node: ForLoopNode):
        """Costo de un bucle FOR (Cormen/Bisbal)."""
        metrics_logger.start_timer("visit_forloop")
        
        # 1. Resolver límites
        start_val = self._resolve_expr(node.start)
        end_val = self._resolve_expr(node.end)
        
        # 2. Calcular iteraciones
        # (end - start + 1)
        try:
            iterations = (end_val - start_val + 1).simplify()
        except Exception:
            iterations = self.n # Fallback si la simplificación falla
            
        # 3. Analizar el cuerpo
        body_cost = node.body.accept(self)
        
        # 4. Costo total = iteraciones * costo_cuerpo
        total_cost = body_cost * iterations
        
        metrics_logger.end_timer("visit_forloop")
        return total_cost

    def visit_IfNode(self, node: IfNode):
        """Costo de un IF-THEN-ELSE (Max/Min)."""
        cond_cost = node.condition.accept(self)
        then_cost = node.then_branch.accept(self)
        
        if node.else_branch:
            else_cost = node.else_branch.accept(self)
        else:
            else_cost = ComplexityResult(sympify(0), sympify(0))
            
        return ComplexityResult.O_Omega_from_branches(cond_cost, then_cost, else_cost)

    def visit_WhileLoopNode(self, node: WhileLoopNode):
        """
        Costo de un bucle WHILE.
        ¡ADVERTENCIA! Determinar las iteraciones de un WHILE
        es indecidible en el caso general.
        
        Estrategia simple: Asumir que se ejecuta 'n' veces
        para el peor caso (O) y 1 vez para el mejor caso (Ω).
        """
        logger.warning(f"Bucle WHILE detectado. Asumiendo O(n) iteraciones, Ω(1) iteraciones.")
        
        cond_cost = node.condition.accept(self)
        body_cost = node.body.accept(self)
        
        # Peor caso: (costo_condicion + costo_cuerpo) * n
        cost_O = (cond_cost.O + body_cost.O) * self.n
        
        # Mejor caso: (costo_condicion) * 1 (el bucle no se ejecuta)
        cost_Omega = cond_cost.Omega
        
        return ComplexityResult(cost_O, cost_Omega)

    def visit_CallNode(self, node: CallNode):
        """
        Costo de una llamada a función.
        (El manejo de recursión se implementaría aquí)
        """
        # TODO: Implementar recursión (Teorema Maestro, Cormen Cap 4)
        logger.warning(f"Llamada a función '{node.func_name}' encontrada. Asumiendo costo O(1) (no recursivo).")
        # Asumir O(1) por ahora
        return ComplexityResult(sympify(1), sympify(1))

    # --- Visitantes de Expresiones (devuelven costo) ---

    def visit_VarNode(self, node: VarNode):
        """Costo de leer una variable (O(1))."""
        return ComplexityResult(sympify(0), sympify(0))
        
    def visit_ConstNode(self, node: ConstNode):
        """Costo de un literal (O(1))."""
        return ComplexityResult(sympify(0), sympify(0))
        
    def visit_BinOpNode(self, node: BinOpNode):
        """Costo de una operación binaria (O(1))."""
        left_cost = node.left.accept(self)
        right_cost = node.right.accept(self)
        return ComplexityResult(sympify(1), sympify(1)) + left_cost + right_cost