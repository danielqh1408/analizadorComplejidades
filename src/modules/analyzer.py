import sympy
from sympy import Symbol, Sum, simplify, O, oo
from src.modules.ast_nodes import ASTVisitor, SequenceNode, ForLoopNode, WhileLoopNode, IfNode, AssignNode, CallNode, FunctionNode, BinOpNode, ConstNode, VarNode, UnaryOpNode

class ComplexityAnalyzer(ASTVisitor):
    def __init__(self):
        # Símbolo global para el tamaño de la entrada 'n'
        self.n = Symbol('n', integer=True, positive=True)
        self.current_function = None
        self.is_recursive = False
        self.recurrence_relation = None

    def analyze(self, ast_node):
        """
        Entrada: Nodo raíz del AST (generalmente FunctionNode o SequenceNode).
        Salida: Diccionario con el análisis de complejidad.
        """
        # Reiniciar estado
        self.is_recursive = False
        self.recurrence_relation = None
        
        # Calcular la expresión de costo exacto (T(n))
        cost_expr = self.visit(ast_node)
        
        # Simplificar la expresión matemática
        cost_expr = simplify(cost_expr)
        
        # Calcular Big-O (Peor caso)
        try:
            # Calculamos el límite cuando n -> infinito para O grande
            big_o = O(cost_expr, (self.n, oo))
        except:
            big_o = "Indeterminado (requiere análisis LLM)"

        return {
            "cost_expression": str(cost_expr),
            "big_o": str(big_o),
            "is_recursive": self.is_recursive,
            "recurrence_equation": str(self.recurrence_relation) if self.is_recursive else None
        }

    # --- Visitantes de Estructuras de Control ---

    def visit_FunctionNode(self, node):
        self.current_function = node.name
        # El costo de una función es el costo de su cuerpo
        return self.visit(node.body)

    def visit_SequenceNode(self, node):
        # El costo de una secuencia es la suma de los costos de sus instrucciones
        total_cost = 0
        for stmt in node.statements:
            total_cost += self.visit(stmt)
        return total_cost

    def visit_ForLoopNode(self, node):
        # Análisis DETERMINISTA de bucles usando Sumatorias
        # 1. Obtener límites. Si son variables desconocidas, asumimos 'n' o constantes.
        start_val = self.visit(node.start)
        end_val = self.visit(node.end)
        
        # Si los límites no son símbolos matemáticos, forzamos 'n' para el análisis asintótico
        if not isinstance(end_val, (sympy.Basic, int)):
            end_val = self.n

        # 2. Calcular costo del cuerpo
        body_cost = self.visit(node.body)
        
        # 3. Crear variable de iteración simbólica
        iter_var = Symbol(node.variable.name)
        
        # 4. La complejidad es la Sumatoria del costo del cuerpo desde start hasta end
        # Sum(Cuerpo, (i, inicio, fin))
        summation = Sum(body_cost, (iter_var, start_val, end_val))
        
        # Intentar resolver la sumatoria (closed form)
        return summation.doit()

    def visit_WhileLoopNode(self, node):
        # Los While son difíciles de predecir determinísticamente.
        # Asumimos peor caso O(n) multiplicado por el cuerpo, o marcamos para el LLM.
        body_cost = self.visit(node.body)
        # Representamos el número de iteraciones como 'n' genérico para análisis de peor caso
        return self.n * body_cost

    def visit_IfNode(self, node):
        # Costo = Costo(Condición) + Max(Costo(Then), Costo(Else))
        cond_cost = self.visit(node.condition)
        then_cost = self.visit(node.then_branch)
        else_cost = self.visit(node.else_branch) if node.else_branch else 0
        
        # Para Big-O (peor caso), tomamos la rama más costosa
        # Usamos una función Max simbólica o simplificamos si son comparables
        try:
            worst_branch = sympy.Max(then_cost, else_cost)
        except:
            worst_branch = then_cost + else_cost # Aproximación conservadora
            
        return cond_cost + worst_branch

    def visit_CallNode(self, node):
        # Detección de Recursividad
        if self.current_function and node.func_name == self.current_function:
            self.is_recursive = True
            # Intentamos extraer el argumento para formar T(n/2) o T(n-1)
            # Esto es una simplificación: tomamos el primer argumento como el reductor
            arg = self.visit(node.args[0]) if node.args else self.n
            
            # Creamos un símbolo de función T
            T = sympy.Function('T')
            term = T(arg)
            
            # Guardamos la relación para el reporte (ej: T(n/2))
            self.recurrence_relation = f"T(n) = ... + {term}"
            return term
        else:
            # Llamada a otra función: Asumimos O(1) si no la conocemos, 
            # o O(n) si es una función de sistema costosa.
            return 1

    # --- Visitantes de Operaciones Básicas (Costo = 1) ---

    def visit_AssignNode(self, node):
        # Asignación cuesta 1 unidad de tiempo + costo de evaluar la expresión
        return 1 + self.visit(node.value)

    def visit_BinOpNode(self, node):
        return 1 # Operación aritmética simple cuesta 1

    def visit_UnaryOpNode(self, node):
        return 1

    def visit_VarNode(self, node):
        # Si la variable es 'n' o una variable de tamaño conocida, devolver el símbolo N
        if node.name.lower() in ['n', 'm', 'size', 'length']:
            return self.n
        return Symbol(node.name) # Devolver como símbolo genérico

    def visit_ConstNode(self, node):
        return node.value