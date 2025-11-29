import sympy
from sympy import Symbol, Sum, simplify, O, oo, Integer, Max, Min, Rational
from src.modules.ast_nodes import ASTVisitor


#Aqui tenemos el analyzer que lo que busca es determinar la complejidad de nuestro
#Algoritmo, aqui se hace el proceso para obtener el mejor,peor y caso promedio del algoritmo
#darnos los costos que cuesta cada linea del codigo proporcionado

#Usa el AST que proporciona el uso del Parser.
class ComplexityAnalyzer(ASTVisitor):
    def __init__(self):
        # Definimos 'n' como entero positivo para ayudar a SymPy a simplificar Max(0, ...)
        self.n = Symbol('n', integer=True, positive=True)
        self.current_mode = 'worst' # worst, best, average
        self.line_costs = {}
        self.is_recursive = False
        self.recurrence_relation = None

    def analyze(self, ast_node):
        #Ejecuta los tres análisis y devuelve el reporte completo.
        
        results = {}
        
        # 1. Peor Caso (Big O)
        self._reset('worst')
        worst_expr = self.visit(ast_node)
        results['worst_case'] = {
            'expr': str(simplify(worst_expr)).replace("**", "^"),
            'notation': f"{O(worst_expr, (self.n, oo))}".replace("**", "^")
        }
        
        # 2. Mejor Caso (Big Omega)
        self._reset('best')
        best_expr = self.visit(ast_node)
        results['best_case'] = {
            'expr': str(simplify(best_expr)).replace("**", "^"),
            'notation': f"{O(best_expr, (self.n, oo))}".replace("O(", "Ω(").replace("**", "^") 
            # Nota: SymPy usa O() para el comportamiento asintótico, lo renombramos visualmente
        }

        # 3. Caso Promedio (Big Theta)
        self._reset('average')
        avg_expr = self.visit(ast_node)
        results['average_case'] = {
            'expr': str(simplify(avg_expr)).replace("**", "^"),
            'notation': f"{O(avg_expr, (self.n, oo))}".replace("O(", "Θ(").replace("**", "^")
        }

        # Metadatos extra
        results['line_costs'] = self.line_costs
        results['is_recursive'] = self.is_recursive
        results['recurrence'] = str(self.recurrence_relation) if self.is_recursive else None
        
        return results

    def _reset(self, mode):
        self.current_mode = mode
        # No reseteamos line_costs aquí para acumular info, o podríamos hacerlo por modo
        # Por simplicidad, guardaremos el desglose del Peor Caso (el más útil)
        if mode == 'worst':
            self.line_costs = {}
            self.is_recursive = False
            self.recurrence_relation = None

    def _record_cost(self, node, cost):
        #Guarda el costo asociado a la línea del nodo (si existe)
        # Asumimos que el parser inyecta el atributo 'line' en los nodos
        if hasattr(node, 'line') and node.line is not None:
            cost_str = str(simplify(cost)).replace("**", "^")
            self.line_costs[node.line] = cost_str
        return cost

    #Extraer valor simbólico para límites de bucles
    def _get_symbolic_value(self, node):
        try:
            if type(node).__name__ == 'ConstNode': return Integer(node.value)
            if type(node).__name__ == 'VarNode': 
                 if str(node.name).upper() in ['N', 'M', 'SIZE', 'LONGITUD', 'CANTIDAD']:
                     return self.n
                 return Symbol(node.name, integer=True)
            if type(node).__name__ == 'BinOpNode':
                left = self._get_symbolic_value(node.left)
                right = self._get_symbolic_value(node.right)
                op_map = {'+': lambda x,y: x+y, '-': lambda x,y: x-y, '*': lambda x,y: x*y, '/': lambda x,y: x/y}
                return op_map.get(node.op, lambda x,y: self.n)(left, right)
            return self.n
        except: return self.n
            
        # Si es algo complejo (vector[i]), asumimos que no afecta los límites o es N
        return self.n

    #Visitantes del costo, estas brindan el costo en variables como 1,N,ec

    def visit_list(self, nodes):
        """Maneja la lista de funciones que devuelve el parser."""
        total_cost = 0
        for node in nodes:
            total_cost += self.visit(node)
        return total_cost

    def visit_FunctionNode(self, node):
        self.current_function = node.name
        return self.visit(node.body)

    def visit_SequenceNode(self, node):
        total_cost = 0
        for stmt in node.statements:
            total_cost += self.visit(stmt)
        return total_cost

    def visit_ForLoopNode(self, node):
        # Límites simbólicos
        start = self._get_symbolic_value(node.start)
        end = self._get_symbolic_value(node.end)
        
        body_cost = self.visit(node.body)
        iter_var = Symbol(node.variable.name, integer=True)
        
        # El For es determinista en iteraciones, igual para todos los casos
        total = Sum(body_cost, (iter_var, start, end)).doit()
        return self._record_cost(node, total)

    def visit_WhileLoopNode(self, node):
        body_cost = self.visit(node.body)
        cond_cost = self.visit(node.condition)
        
        if self.current_mode == 'worst':
            total = self.n * (body_cost + cond_cost)
        elif self.current_mode == 'best':
            total = cond_cost
        else: # average
            total = (self.n / 2) * (body_cost + cond_cost)
            
        return self._record_cost(node, total)

    def visit_IfNode(self, node):
        cond_cost = self.visit(node.condition)
        then_cost = self.visit(node.then_branch)
        else_cost = self.visit(node.else_branch) if node.else_branch else 0
        
        if self.current_mode == 'worst':
            branch_cost = Max(then_cost, else_cost)
        elif self.current_mode == 'best':
            branch_cost = Min(then_cost, else_cost)
        else: # average
            prob = Rational(1, 2) 
            branch_cost = (prob * then_cost) + (prob * else_cost)
            
        total = cond_cost + branch_cost
        return self._record_cost(node, total)

    def visit_CallNode(self, node):
        if self.current_function and node.func_name == self.current_function:
            self.is_recursive = True
            # Recurrencia detectada
            arg_val = self._get_symbolic_value(node.args[0]) if node.args else self.n
            T = sympy.Function('T')
            self.recurrence_relation = f"T(n) = ... + T({arg_val})"
            return T(arg_val)
        return 1 # Llamada externa cuesta 1

    #Operaciones Básicas
    
    def visit_AssignNode(self, node):
        cost = 1 + self.visit(node.value)
        return self._record_cost(node, cost)

    def visit_BinOpNode(self, node):
        return 1 # a + b cuesta 1 ciclo

    def visit_UnaryOpNode(self, node):
        return 1

    def visit_VarNode(self, node):
        return 1 # Leer memoria cuesta 1 ciclo

    def visit_ConstNode(self, node):
        return 1 # Leer constante cuesta 1 ciclo