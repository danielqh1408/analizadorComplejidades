from lark import Lark, Transformer, v_args
from src.modules.ast_nodes import *

# --- Gramática de Lark (Robusta: CALL opcional) ---
PSEUDOCODE_GRAMMAR = r"""
    ?start: function+ -> start_node

    function: "FUNCTION" ID "(" [param_list] ")" "BEGIN" sequence "END" -> function_node
    param_list: ID ("," ID)* -> param_list

    ?statement: "BEGIN" sequence "END" -> sequence_node 
              | assign_statement
              | for_loop
              | while_loop
              | if_statement
              | call_statement  // El orden importa poco aquí gracias a Lark
    
    sequence: statement* -> sequence_node

    // Asignación (ID <- val o Array[...] <- val)
    assign_statement: (ID | array_access) ASSIGN expression -> assign_node
    
    // Bucles
    for_loop: "FOR" ID ASSIGN expression "TO" expression "DO" statement -> for_loop_node
    while_loop: "WHILE" "(" expression ")" "DO" statement -> while_loop_node
    
    // Condicionales
    if_statement: "IF" "(" expression ")" "THEN" statement ["ELSE" statement] -> if_node
    
    // --- CORRECCIÓN AQUÍ: CALL es opcional ("CALL"? significa 0 o 1 vez) ---
    call_statement: "CALL"? ID "(" [arg_list] ")" -> call_node
    
    arg_list: expression ("," expression)* -> arg_list

    // Expresiones
    ?expression: bool_or_expr
    ?bool_or_expr: bool_and_expr (OR bool_and_expr)* -> bin_op
    ?bool_and_expr: comp_expr (AND comp_expr)* -> bin_op
    
    ?comp_expr: arith_expr ((GT | LT | GTE | LTE | EQ | NEQ) arith_expr)* -> bin_op
    
    ?arith_expr: term ((PLUS | MINUS) term)* -> bin_op
    ?term: factor ((STAR | SLASH) factor)* -> bin_op
    ?factor: (PLUS | MINUS | NOT) factor -> unary_op
           | atom
    
    ?atom: NUMBER -> const_node
         | ID -> var_node
         | array_access
         | "(" expression ")"

    array_access: ID ("[" expression "]")+ -> array_access_node

    // --- TERMINALES ---
    ASSIGN: "<-"
    ID: /[a-zA-Z_][a-zA-Z0-9_]*/
    NUMBER: /[0-9]+/

    PLUS: "+"
    MINUS: "-"
    STAR: "*"
    SLASH: "/"
    
    GTE: ">="
    LTE: "<="
    NEQ: "!=" | "<>"
    GT: ">"
    LT: "<"
    EQ: "="
    
    AND: /and/i
    OR: /or/i
    NOT: /not/i
    FOR: /for/i
    TO: /to/i
    DO: /do/i
    WHILE: /while/i
    IF: /if/i
    THEN: /then/i
    ELSE: /else/i
    BEGIN: /begin/i
    END: /end/i
    CALL: /call/i
    FUNCTION: /function/i

    COMMENT: /\/\/[^\n]*/
    %import common.WS
    %ignore WS
    %ignore COMMENT
"""

@v_args(inline=True)
class AstTransformer(Transformer):
    def __init__(self):
        self.str = str
        self.int = int
    
    def start_node(self, *functions): return list(functions)
    def var_node(self, name): return VarNode(name=str(name))
    def const_node(self, value): return ConstNode(value=int(value))

    def array_access_node(self, name, *indices):
        return VarNode(name=f"{name}_multidim") 

    def unary_op(self, op, operand): return UnaryOpNode(op=str(op), operand=operand)

    def bin_op(self, *args):
        if len(args) == 1: return args[0]
        left = args[0]
        i = 1
        while i + 1 < len(args):
            op = args[i]
            right = args[i + 1]
            left = BinOpNode(left=left, op=str(op), right=right)
            i += 2
        return left

    def assign_node(self, target, assign_op, value):
        target_node = target if isinstance(target, VarNode) else VarNode(name=str(target))
        return AssignNode(target=target_node, value=value)
    
    def sequence_node(self, *statements):
        flat = []
        for s in statements:
            if isinstance(s, list): flat.extend(s)
            else: flat.append(s)
        return SequenceNode(statements=flat)

    def for_loop_node(self, var_id, assign_op, start, end, body):
        if not isinstance(body, SequenceNode): body = SequenceNode([body])
        return ForLoopNode(variable=VarNode(str(var_id)), start=start, end=end, body=body)
    
    def while_loop_node(self, cond, body):
        if not isinstance(body, SequenceNode): body = SequenceNode([body])
        return WhileLoopNode(condition=cond, body=body)
    
    def if_node(self, cond, then_b, else_b=None):
        if not isinstance(then_b, SequenceNode): then_b = SequenceNode([then_b])
        if else_b and not isinstance(else_b, SequenceNode): else_b = SequenceNode([else_b])
        return IfNode(condition=cond, then_branch=then_b, else_branch=else_b)
    
    def call_node(self, name, args=None):
        # El argumento 'name' puede venir solo (si no hay CALL) o tras CALL.
        # Lark a veces lo simplifica. El nombre de la función siempre es el token ID.
        safe_args = args if args else []
        if hasattr(safe_args, 'children'): safe_args = safe_args.children
        return CallNode(func_name=str(name), args=list(safe_args) if isinstance(safe_args, tuple) else safe_args)
        
    def function_node(self, name, params, body):
        safe_params = params if params else []
        if hasattr(safe_params, 'children'): safe_params = safe_params.children
        return FunctionNode(name=str(name), params=list(safe_params), body=body)

    def param_list(self, *items):
        return [VarNode(str(item)) for item in items if item.type == 'ID']
    
    def arg_list(self, *args):
        return list(args)

class PseudocodeParser:
    def __init__(self):
        self.parser = Lark(PSEUDOCODE_GRAMMAR, parser='lalr', lexer='contextual', start='start')
        self.transformer = AstTransformer()

    def parse_text(self, code: str):
        try:
            tree = self.parser.parse(code)
            return self.transformer.transform(tree)
        except Exception as e:
            raise SyntaxError(f"Error parsing: {e}")