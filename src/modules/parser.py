"""
Módulo Parser (Analizador Sintáctico)

Este módulo utiliza 'lark-parser' (definido en el stack del proyecto)
para convertir una secuencia de tokens (del Lexer) en un Árbol de
Sintaxis Abstracta (AST) basado en 'ast_nodes.py'.
"""

from lark import Lark, Transformer, v_args
from src.modules.lexer import Token
from src.modules.ast_nodes import *

# --- Gramática de Lark (basada en Proyecto_Gramatica.docx) ---
# Esta gramática define la sintaxis que el parser aceptará.
PSEUDOCODE_GRAMMAR = r"""
    ?start: function+ -> start_node

    function: "FUNCTION" ID "(" [param_list] ")" "BEGIN" sequence "END" -> function_node
    param_list: ID ("," ID)* -> param_list

    ?statement: "BEGIN" sequence "END" -> sequence_node  // Bloque explícito
              | assign_statement
              | for_loop
              | while_loop
              | if_statement
              | call_statement
    
    sequence: statement* -> sequence_node

    assign_statement: ID ASSIGN expression -> assign_node
    
    for_loop: "FOR" ID ASSIGN expression "TO" expression "DO" statement -> for_loop_node
    
    while_loop: "WHILE" "(" expression ")" "DO" statement -> while_loop_node
    
    if_statement: "IF" "(" expression ")" "THEN" statement ["ELSE" statement] -> if_node
    
    call_statement: "CALL" ID "(" [arg_list] ")" -> call_node
    arg_list: expression ("," expression)* -> arg_list

    ?expression: bool_or_expr
    
    ?bool_or_expr: bool_and_expr (OR bool_and_expr)* -> bin_op
    ?bool_and_expr: comp_expr (AND comp_expr)* -> bin_op
    
    // Regla para operadores de comparación
    ?comp_expr: arith_expr (REL_OP arith_expr)* -> bin_op
    
    // Tus reglas aritméticas (solo renombradas)
    ?arith_expr: term ((PLUS | MINUS) term)* -> bin_op
    ?term: factor ((STAR | SLASH) factor)* -> bin_op
    
    // Manejo de 'NOT' (unario) y paréntesis
    ?factor: NOT factor                            -> unary_op
           | atom
    
    ?atom: NUMBER                                -> const_node
         | ID                                  -> var_node
         | "(" expression ")"                  // Vuelve a la regla principal
         
    // --- Terminales personalizados ---
    ASSIGN: "🡨"
    ID: /[a-zA-Z_][a-zA-Z0-9_]*/
    NUMBER: /[0-9]+/

    // --- Terminales Aritméticos ---
    PLUS: "+"
    MINUS: "-"
    STAR: "*"
    SLASH: "/"
    
    // --- Terminales Relacionales (LOS QUE FALTABAN) ---
    GT: ">"
    LT: "<"
    GTE: "≥"
    LTE: "≤"
    EQ: "="
    NEQ: "≠"
    
    // Agrupación para la regla comp_expr
    REL_OP: GT | LT | GTE | LTE | EQ | NEQ

    // --- Terminales Booleanos (LOS QUE FALTABAN) ---
    AND: "and"
    OR: "or"
    NOT: "not"
    
    // --- Palabras Clave ---
    FOR: "FOR"
    TO: "TO"
    DO: "DO"
    WHILE: "WHILE"
    IF: "IF"
    THEN: "THEN"
    ELSE: "ELSE"
    BEGIN: "BEGIN"
    END: "END"
    CALL: "CALL"
    FUNCTION: "FUNCTION"

    COMMENT: /\/\/[^\n]*/
    NEWLINE: /(\r?\n)+/

    %import common.WS
    %ignore WS
    %ignore COMMENT
    %ignore NEWLINE
"""

# --- Transformador de AST ---
@v_args(inline=True) # Simplifica los métodos del transformer
class AstTransformer(Transformer):
    """
    Transforma el árbol de parseo de Lark en nuestro AST personalizado.
    Cada método aquí corresponde a una regla en la gramática.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convertir tokens de Lark a nuestros nodos
        self.str = str
        self.int = int
        self.float = float
    
    # --- Nodos de Expresión ---
    def start_node(self, *functions):
        print("🌱 Método start_node ejecutado correctamente")
        return list(functions)

    def var_node(self, name):
        return VarNode(name=str(name))
        
    def const_node(self, value):
        return ConstNode(value=int(value.value)) # .value del token
    
    def unary_op(self, op, operand):
        """Maneja operadores unarios como 'NOT'."""
        return UnaryOpNode(op=str(op), operand=operand)

    def bin_op(self, *args):
        """
        Construye un árbol binario para expresiones como a + b - c * d.
        Corrige posibles desajustes si la gramática entrega un número impar de args.
        """
        if len(args) == 1:
            return args[0]

        left = args[0]
        i = 1
        while i + 1 < len(args):  # evita "out of range"
            op = args[i]
            right = args[i + 1]
            left = BinOpNode(left=left, op=str(op), right=right)
            i += 2

        # Si la gramática deja un operador colgante (raro, pero por seguridad)
        if i < len(args):
            print(f"⚠️ Advertencia: bin_op recibió args impares: {args}")

        return left

    # --- Nodos de Sentencia ---
    def assign_node(self, target_id, assign_op, value_expr):
        print("✅ MÉTODO assign_node CORRECTO EJECUTADO")
        return AssignNode(target=VarNode(name=str(target_id)), value=value_expr)
    
    def sequence_node(self, *statements):
        return SequenceNode(statements=list(statements))

    def for_loop_node(self, var_id, assign_op, start_expr, end_expr, body_statement):
        # Asegurar que el cuerpo sea siempre una secuencia
        if not isinstance(body_statement, SequenceNode):
            body_statement = SequenceNode(statements=[body_statement])
    
        # El resto de la lógica es la misma, 'assign_op' simplemente se ignora
        return ForLoopNode(
            variable=VarNode(name=str(var_id)), 
            start=start_expr, 
            end=end_expr, 
            body=body_statement
        )

    def if_node(self, cond, then_branch, else_branch=None):
        if not isinstance(then_branch, SequenceNode):
            then_branch = SequenceNode(statements=[then_branch])
        if else_branch and not isinstance(else_branch, SequenceNode):
            else_branch = SequenceNode(statements=[else_branch])
            
        return IfNode(
            condition=cond, 
            then_branch=then_branch, 
            else_branch=else_branch
        )

    def while_loop_node(self, cond, body_statement):
        if not isinstance(body_statement, SequenceNode):
            body_statement = SequenceNode(statements=[body_statement])
        return WhileLoopNode(condition=cond, body=body_statement)

    def call_node(self, func_name, args=None):
        # Si args viene como tupla, conviértelo a lista
        if isinstance(args, tuple):
            args_list = list(args)
        elif hasattr(args, "children"):
            args_list = args.children
        elif isinstance(args, list):
            args_list = args
        elif args is None:
            args_list = []
        else:
            args_list = [args]
            
        return CallNode(func_name=str(func_name), args=args_list)
        
    def arg_list(self, *args):
        return args
    
    def param_list(self, *items):
        """
        Transforma la lista de parámetros de una función.
        'items' será una tupla de Tokens (ID, COMMA, ID, ...)
        """
        # Filtramos solo los tokens de ID y los convertimos a VarNode
        # str(item) funciona porque Lark convierte el Token a su valor
        return [VarNode(name=str(item)) for item in items if item.type == 'ID']

    # --- Nodos de Alto Nivel ---
    def function_node(self, name, params, body):
        """
        Construye un nodo de función.
        Corrige el manejo de parámetros cuando param_list devuelve una lista nativa.
        """
        param_nodes = list(params) if params else []
        # Si params es None o ya una lista, la usamos directamente
        if params is None:
            param_nodes = []
        elif isinstance(params, list):
            param_nodes = params
        else:
            # En caso raro de que la gramática devuelva un Tree
            param_nodes = params.children

        return FunctionNode(
            name=str(name),
            params=param_nodes,
            body=body
        )

    def sequence_node(self, *statements):
        """
        Captura el bloque BEGIN ... END y lo convierte en SequenceNode.
        """
        from lark import Tree

        flat_statements = []

        for s in statements:
            # Si Lark envía subárboles tipo Tree, intenta convertirlos
            if isinstance(s, Tree):
                if hasattr(s, 'children'):
                    flat_statements.extend(s.children)
                else:
                    flat_statements.append(s)
            elif isinstance(s, list):
                flat_statements.extend(s)
            else:
                flat_statements.append(s)

        return SequenceNode(statements=flat_statements)



# --- Clase Principal del Parser ---

class PseudocodeParser:
    """
    Implementa el analizador sintáctico.
    
    Propósito: Convertir una lista de Tokens en un AST.
    Método: Utiliza Lark con una gramática definida y un transformador.
    Complejidad: O(N) (lineal con el número de tokens),
                 típico de parsers LALR como Lark.
    """
    def __init__(self):
        try:
            # Inicializa el parser de Lark
            self.transformer = AstTransformer()

            self.parser = Lark(
                PSEUDOCODE_GRAMMAR,
                parser='lalr',
                lexer='contextual',
                start='start'
            )
        except Exception as e:
            print(f"Error al inicializar el parser de Lark: {e}")
            raise
        
    def parse_text(self, code: str):
        """
        Parsea el código fuente del pseudocódigo y devuelve el AST transformado.
        """
        try:
            # Primero obtenemos el árbol crudo de Lark
            tree = self.parser.parse(code)
            print("🌲 Árbol Lark generado correctamente:", type(tree))

            # Aplicamos nuestro transformador personalizado
            ast = AstTransformer().transform(tree)
            print("✅ AST transformado:", type(ast))

            return ast

        except Exception as e:
            raise SyntaxError(f"Error de sintaxis en el pseudocódigo: {e}")
