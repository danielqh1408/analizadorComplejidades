import sympy
from sympy import Symbol, Sum, simplify, O, oo, Integer
from src.modules.ast_nodes import ASTVisitor

class ComplexityAnalyzer(ASTVisitor):
    def __init__(self):
        # Definimos 'n' como entero positivo para ayudar a SymPy a simplificar Max(0, ...)
        self.n = Symbol('n', integer=True, positive=True)
        self.current_function = None
        self.is_recursive = False
        self.recurrence_relation = None

    def analyze(self, ast_node):
        self.is_recursive = False
        self.recurrence_relation = None
        
        # Calculamos el COSTO (T(n))
        cost_expr = self.visit(ast_node)
        
        # Simplificación agresiva
        cost_expr = simplify(cost_expr)
        
        # Calcular Big-O
        try:
            big_o = O(cost_expr, (self.n, oo))
        except:
            big_o = "Indeterminado"

        return {
            "cost_expression": str(cost_expr).replace("**", "^"), # Formato bonito
            "big_o": str(big_o).replace("**", "^"),
            "is_recursive": self.is_recursive,
            "recurrence_equation": str(self.recurrence_relation) if self.is_recursive else None
        }

    # --- HELPER: Extraer valor simbólico para límites de bucles ---
    def _get_symbolic_value(self, node):
        """Devuelve el SÍMBOLO matemático (N) o el número (0, 1)"""
        node_type = type(node).__name__
        
        if node_type == 'VarNode':
            # Si la variable es N, M, Size, es nuestro símbolo de complejidad
            if str(node.name).upper() in ['N', 'M', 'SIZE', 'LONGITUD', 'CANTIDAD']:
                return self.n
            # Si es una variable de control (i, j), la devolvemos como símbolo para la sumatoria
            return Symbol(node.name, integer=True)
        
        if node_type == 'ConstNode':
            return Integer(node.value)
            
        if node_type == 'BinOpNode':
            left = self._get_symbolic_value(node.left)
            right = self._get_symbolic_value(node.right)
            if node.op == '+': return left + right
            if node.op == '-': return left - right
            if node.op == '*': return left * right
            if node.op == '/': return left / right
            
        # Si es algo complejo (vector[i]), asumimos que no afecta los límites o es N
        return self.n

    # --- Visitantes de COSTO (Retornan unidades de tiempo: 1, N, etc.) ---

    def visit_FunctionNode(self, node):
        self.current_function = node.name
        return self.visit(node.body)

    def visit_SequenceNode(self, node):
        total_cost = 0
        for stmt in node.statements:
            total_cost += self.visit(stmt)
        return total_cost

    def visit_ForLoopNode(self, node):
        # 1. Obtener límites SIMBÓLICOS (no costo)
        start_val = self._get_symbolic_value(node.start)
        end_val = self._get_symbolic_value(node.end)
        
        # 2. Calcular costo del cuerpo
        body_cost = self.visit(node.body)
        
        # 3. Sumatoria
        iter_var = Symbol(node.variable.name, integer=True)
        
        # Costo del bucle: Suma(Cuerpo) + Costo de evaluar límites y saltos
        # Simplificación: Suma(Cuerpo, start, end)
        summation = Sum(body_cost, (iter_var, start_val, end_val))
        
        return summation.doit()

    def visit_WhileLoopNode(self, node):
        # Estimación de peor caso para While: O(N) * cuerpo
        body_cost = self.visit(node.body)
        return self.n * body_cost

    def visit_IfNode(self, node):
        cond_cost = self.visit(node.condition)
        then_cost = self.visit(node.then_branch)
        else_cost = self.visit(node.else_branch) if node.else_branch else 0
        # Peor caso: la rama más cara
        return cond_cost + sympy.Max(then_cost, else_cost)

    def visit_CallNode(self, node):
        if self.current_function and node.func_name == self.current_function:
            self.is_recursive = True
            # Recurrencia detectada
            arg_val = self._get_symbolic_value(node.args[0]) if node.args else self.n
            T = sympy.Function('T')
            self.recurrence_relation = f"T(n) = ... + T({arg_val})"
            return T(arg_val)
        return 1 # Llamada externa cuesta 1

    # --- Operaciones Básicas ---
    # CORRECCIÓN CRÍTICA: Estas retornan COSTO CONSTANTE (1), no el símbolo
    
    def visit_AssignNode(self, node):
        return 1 + self.visit(node.value) # Costo asignación + costo evaluar expr

    def visit_BinOpNode(self, node):
        return 1 # a + b cuesta 1 ciclo

    def visit_UnaryOpNode(self, node):
        return 1

    def visit_VarNode(self, node):
        return 1 # Leer memoria cuesta 1 ciclo (¡Aquí estaba el error!)

    def visit_ConstNode(self, node):
        return 1 # Leer constante cuesta 1 ciclo