"""
Motor de Análisis de Complejidad (AST Walker)

Este módulo implementa el Visitor que recorre el AST (generado por
'parser.py') y calcula la complejidad simbólica.

Utiliza 'sympy' para manejar expresiones matemáticas.
La lógica se basa en los principios de análisis de algoritmos de
Cormen (ej. Cap 2, Cap 4) y Bisbal (ej. Cap 2).

*** Actualización: Se ha implementado el soporte para recursión
    detectando llamadas y aplicando el Teorema Maestro. ***
"""

import sympy
from sympy import Symbol, sympify, Max, Min, oo, log
from typing import Dict, Any, Optional, List

# Importar nodos y servicios del proyecto
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
        # Asegurarse de que el multiplicador sea una expresión de sympy
        if not isinstance(other, sympy.Expr):
            other = sympify(other)
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
    
    Soporta análisis iterativo y recursivo (vía Teorema Maestro).
    """
    
    def __init__(self):
        # Símbolo principal para el análisis
        self.n = Symbol('n', integer=True, positive=True)
        # Símbolos para iteradores de bucles
        self.i = Symbol('i', integer=True)
        self.j = Symbol('j', integer=True)
        self.k = Symbol('k', integer=True)
        
        # Almacena los costos *resueltos* de las funciones
        self.function_costs: Dict[str, ComplexityResult] = {}
        
        # --- Estado de Recursión ---
        self.current_function_name: Optional[str] = None
        # Almacena los parámetros de recursión (a, b) por función
        # E.g.: {"MergeSort": {"a": 2, "b_list": [2, 2]}}
        self.recursion_info: Dict[str, Dict[str, Any]] = {}

    def analyze(self, ast_nodes: List[FunctionNode]) -> Dict[str, Any]:
        """
        Punto de entrada principal. Analiza una lista de funciones
        y devuelve un diccionario de complejidades para la primera función.
        """
        metrics_logger.start_timer("analysis_total")
        
        # 1. Analizar todas las funciones (pobla self.function_costs)
        for func_node in ast_nodes:
            self.visit(func_node)
            
        # 2. Devolver el análisis de la *primera* función
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
        Extrae el término dominante de una expresión de sympy
        usando la notación O.
        """
        expr = expr.simplify()
        if expr == 0:
            return sympify(1) # O(1)
        
        # sympy.O(expr) calcula el orden de crecimiento
        order = sympy.O(expr, (self.n, oo))
        
        if not order.args:
            # Caso O(1)
            return sympify(1)
        
        # O(n**2 + n).args[0] es n**2
        # O(n*log(n)).args[0] es n*log(n)
        dominant_term = order.args[0]

        replacements = {
            log(1 / self.n): log(self.n),
            log(self.n ** (-1)): log(self.n),
            log(self.n / 1): log(self.n)
        }
        dominant_term = dominant_term.xreplace(replacements)
        
        return dominant_term

    def _resolve_expr(self, expr_node: Expression) -> sympy.Expr:
        """Convierte un nodo de expresión del AST a un símbolo de sympy."""
        if isinstance(expr_node, VarNode):
            if expr_node.name == 'n':
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
        self.current_function_name = node.name
        
        # Inicializar estado de recursión para esta función
        self.recursion_info[node.name] = {"a": 0, "b_list": []}

        # 1. Visitar el cuerpo.
        # Los visitantes de nodos (Assign, For, etc.) sumarán el costo local (f(n)).
        # visit_CallNode (si es recursivo) poblará 'recursion_info'
        # y retornará un costo local de 0.
        
        f_n_cost = node.body.accept(self)
        
        # 2. Post-visita: Resolver la recursión si existe
        rec_info = self.recursion_info[node.name]
        a = rec_info["a"]
        
        if a > 0:
            # --- Es una función recursiva ---
            logger.debug(f"Función recursiva detectada: {node.name}. a={a}")
            
            # 3. Validar 'b' (T(n/b))
            if not rec_info["b_list"]:
                logger.warning(f"Llamadas recursivas T(n) sin reducción de problema. Asumiendo O(inf).")
                b = sympify(1) # T(n) = aT(n) + f(n) -> Infinito
            else:
                b = rec_info["b_list"][0] # Tomar el primer 'b'
                # Validar que todas las llamadas recursivas sean T(n/b)
                if not all(val == b for val in rec_info["b_list"]):
                    logger.warning(f"Llamadas recursivas mixtas detectadas (ej. T(n/2) y T(n/3)). No se puede aplicar el Teorema Maestro.")
                    # Fallback: No se puede resolver. Devolver solo el trabajo local.
                    self.function_costs[node.name] = f_n_cost
                    self.current_function_name = None
                    return f_n_cost
            
            # 4. Aplicar Teorema Maestro
            logger.debug(f"Aplicando Teorema Maestro: a={a}, b={b}, f(n)={f_n_cost.O}")
            solved_cost = self._apply_master_theorem(a, b, f_n_cost)
            self.function_costs[node.name] = solved_cost
            
        else:
            # --- No es una función recursiva ---
            self.function_costs[node.name] = f_n_cost
            
        self.current_function_name = None
        return self.function_costs[node.name]

    def visit_SequenceNode(self, node: SequenceNode):
        """Suma los costos de las sentencias secuenciales."""
        cost = ComplexityResult(sympify(0), sympify(0))
        for stmt in node.statements:
            cost += stmt.accept(self)
        return cost

    def visit_AssignNode(self, node: AssignNode):
        """Costo constante (O(1)) para asignación."""
        expr_cost = node.value.accept(self)
        # El costo de f(n) es 1 (asignación) + costo de la expresión
        return ComplexityResult(sympify(1), sympify(1)) + expr_cost

    def visit_ForLoopNode(self, node: ForLoopNode):
        """Costo de un bucle FOR (Cormen/Bisbal)."""
        metrics_logger.start_timer("visit_forloop")
        
        start_val = self._resolve_expr(node.start)
        end_val = self._resolve_expr(node.end)
        
        try:
            iterations = (end_val - start_val + 1).simplify()
        except Exception:
            iterations = (end_val - start_val + 1)
            
        body_cost = node.body.accept(self)
        
        # Costo total = iteraciones * costo_cuerpo
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
            # Si no hay ELSE, el costo es 0 (o O(1) si consideramos
            # la evaluación como un salto)
            else_cost = ComplexityResult(sympify(1), sympify(1))
            
        return ComplexityResult.O_Omega_from_branches(cond_cost, then_cost, else_cost)

    def visit_WhileLoopNode(self, node: WhileLoopNode):
        """
        Costo de un bucle WHILE.
        Estrategia simple: Asumir O(n) iteraciones (peor caso)
        y O(1) iteraciones (mejor caso, el bucle no se ejecuta).
        """
        logger.warning(f"Bucle WHILE detectado. Asumiendo O(n) iteraciones, Ω(1) iteraciones.")
        
        cond_cost = node.condition.accept(self)
        body_cost = node.body.accept(self)
        
        # Peor caso: O(1) (cond) + (O(cond) + O(body)) * n
        cost_O = cond_cost.O + (cond_cost.O + body_cost.O) * self.n
        
        # Mejor caso: O(1) (solo la primera condición)
        cost_Omega = cond_cost.Omega
        
        return ComplexityResult(cost_O, cost_Omega)

    def visit_CallNode(self, node: CallNode):
        """
        Costo de una llamada a función.
        Aquí se implementa la detección de recursión.
        """
        
        if node.func_name == self.current_function_name:
            # --- ¡Llamada recursiva detectada! ---
            logger.debug(f"Llamada recursiva detectada: {node.func_name}")
            
            # 1. Incrementar 'a' (conteo de llamadas)
            self.recursion_info[self.current_function_name]["a"] += 1
            
            # 2. Encontrar 'b' (divisor del problema)
            b_val = self._find_recursion_divider(node.args)
            if b_val:
                self.recursion_info[self.current_function_name]["b_list"].append(b_val)
                
            # 3. Retornar costo CERO
            # El costo de la llamada T(n/b) no es parte del
            # trabajo local f(n).
            return ComplexityResult(sympify(0), sympify(0))
        
        else:
            # --- Llamada no recursiva (externa) ---
            # Comprobar si ya hemos analizado esta función
            if node.func_name in self.function_costs:
                logger.debug(f"Usando costo cacheado para '{node.func_name}'")
                return self.function_costs[node.func_name]
            
            # Si no, asumimos O(1)
            logger.warning(f"Llamada a función externa/no analizada '{node.func_name}'. Asumiendo costo O(1).")
            return ComplexityResult(sympify(1), sympify(1))

    # --- Visitantes de Expresiones (devuelven costo O(1)) ---

    def visit_VarNode(self, node: VarNode):
        """Costo de leer una variable (O(1))."""
        return ComplexityResult(sympify(1), sympify(1))
        
    def visit_ConstNode(self, node: ConstNode):
        """Costo de un literal (O(1))."""
        return ComplexityResult(sympify(1), sympify(1))
        
    def visit_BinOpNode(self, node: BinOpNode):
        """Costo de una operación binaria (O(1))."""
        # El costo es 1 (la operación) + el costo de evaluar los operandos
        left_cost = node.left.accept(self)
        right_cost = node.right.accept(self)
        return ComplexityResult(sympify(1), sympify(1)) + left_cost + right_cost

    # --- Helpers de Recursión ---

    def _find_recursion_divider(self, args: List[Expression]) -> Optional[sympy.Expr]:
        """
        Intenta encontrar el divisor 'b' en T(n/b)
        analizando los argumentos de la llamada recursiva.
        """
        # Asumir que el primer argumento es el tamaño del problema
        if not args:
            return None
            
        arg_expr_node = args[0]
        
        # Convertir el nodo de AST a expresión de sympy
        # (usamos _resolve_expr, que define 'n' como el símbolo)
        arg_expr = self._resolve_expr(arg_expr_node) # ej. n/2
        
        # Intentar aislar 'b' de 'n/b'
        # (n/b) en sympy es n * (1/b)
        if arg_expr.is_Mul and self.n in arg_expr.args:
            # Es de la forma n * (1/b)
            b_inv = arg_expr.subs(self.n, 1) # Reemplaza n por 1, queda 1/b
            if b_inv != 0:
                b_val = (1 / b_inv).simplify()
                logger.debug(f"Divisor 'b' encontrado: {b_val}")
                return b_val
        
        # TODO: Manejar T(n-c) (no aplica al Teorema Maestro)
        if arg_expr.is_Add and self.n in arg_expr.args:
             c = arg_expr.subs(self.n, 0)
             if c < 0:
                 logger.debug(f"Recursión sustractiva detectada: T(n{c}). No se aplica Teorema Maestro.")

        logger.warning(f"No se pudo determinar 'b' de la expresión: {arg_expr}")
        return None

    def _apply_master_theorem(self, a: int, b: sympy.Expr, f_n_cost: ComplexityResult) -> ComplexityResult:
        """
        Aplica el Teorema Maestro (Cormen, Cap 4.5)
        T(n) = aT(n/b) + f(n)

        Compara f(n) con n^(c_crit) donde c_crit = log_b(a)
        Devuelve un ComplexityResult con cotas ajustadas (Theta).
        """
        if b <= 1:
            logger.warning("Divisor de recursión 'b' <= 1. No se puede aplicar Teorema Maestro.")
            return f_n_cost  # Devuelve solo el costo local

        try:
            # 1. Calcular c_crit = log_b(a)
            c_crit = log(a, b)

            # 2. Tomar f(n) (trabajo local del peor caso)
            f_n = f_n_cost.O.simplify()
            if f_n == 0:
                f_n = sympify(1)  # Mínimo O(1)

            # 3. Comparar f(n) con n^c_crit mediante el método del límite
            n_c_crit = self.n ** c_crit
            lim = sympy.limit(f_n / n_c_crit, self.n, oo)

            # --- Aplicar los 3 Casos del Teorema Maestro ---
            if lim == 0:
                # Caso 1: f(n) = O(n^(c_crit - ε))
                logger.debug("Teorema Maestro: Caso 1 (f(n) < n^c_crit)")
                T_n = n_c_crit  # Θ(n^c_crit)

            elif lim.is_finite and lim > 0:
                # Caso 2: f(n) = Θ(n^c_crit)
                logger.debug("Teorema Maestro: Caso 2 (f(n) == n^c_crit)")
                T_n = n_c_crit * log(self.n)  # Θ(n^c_crit * log n)

            elif lim == oo:
                # Caso 3: f(n) = Ω(n^(c_crit + ε))
                logger.debug("Teorema Maestro: Caso 3 (f(n) > n^c_crit)")
                T_n = f_n  # Θ(f(n))

            else:
                logger.warning(f"Límite indeterminado ({lim}). No se puede aplicar Teorema Maestro.")
                return f_n_cost  # Fallback

            # --- 🔧 Normalización simbólica del logaritmo ---
            T_n = T_n.simplify()

            # Reemplazar log(1/n), log(n**(-1)) o log(n/1) por log(n)
            replacements = {
                log(1 / self.n): log(self.n),
                log(self.n ** (-1)): log(self.n),
                log(self.n / 1): log(self.n)
            }
            T_n = T_n.xreplace(replacements)

            # --- Resultado final (Θ idéntica para O y Ω) ---
            T_n = T_n.simplify()
            return ComplexityResult(T_n, T_n)

        except Exception as e:
            logger.error(f"Error al aplicar Teorema Maestro: {e}", exc_info=True)
            return f_n_cost  # Fallback si algo falla
