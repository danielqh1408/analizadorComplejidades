from lark import Lark, Transformer, v_args
from src.modules.ast_nodes import *

# --- Gramática de Lark (Versión Final: Flexible y Robusta) ---
PSEUDOCODE_GRAMMAR = r"""
    ?start: function+ -> start_node

    function: "FUNCTION" ID "(" [param_list] ")" "BEGIN" sequence "END" -> function_node
    
    param_list: param ("," param)* -> param_list
    param: VAR? ID ID? -> param_node

    ?statement: "BEGIN" sequence "END" -> sequence_node 
              | assign_statement
              | declaration_statement
              | for_loop
              | while_loop
              | if_statement
              | call_statement
    
    sequence: statement* -> sequence_node

    // Declaraciones
    declaration_statement: VAR decl_item ("," decl_item)* -> declaration_node
    decl_item: ID array_suffix? type_annotation? init_value?
    array_suffix: ("[" expression "]")+ 
    type_annotation: ":" ID
    init_value: ASSIGN expression

    // Asignación
    assign_statement: (ID | array_access) ASSIGN expression -> assign_node
    
    // Bucles
    for_loop: "FOR" ID ASSIGN expression "TO" expression "DO" statement -> for_loop_node
    while_loop: "WHILE" expression "DO" statement -> while_loop_node

    if_statement: "IF" expression "THEN" statement ["ELSE" statement] -> if_node

    call_statement: "CALL"? ID "(" [arg_list] ")" -> call_node
    arg_list: expression ("," expression)* -> arg_list

    // Expresiones
    ?expression: bool_or_expr
    ?bool_or_expr: bool_and_expr (OR bool_and_expr)* -> bin_op
    ?bool_and_expr: comp_expr (AND comp_expr)* -> bin_op
    ?comp_expr: arith_expr ((GT | LT | GTE | LTE | EQ | NEQ) arith_expr)* -> bin_op
    ?arith_expr: term ((PLUS | MINUS) term)* -> bin_op
    ?term: factor ((STAR | SLASH | MOD | DIV) factor)* -> bin_op
    
    ?factor: (PLUS | MINUS | NOT) factor -> unary_op
           | atom
    
    ?atom: NUMBER -> const_node
         | STRING -> string_node
         | function_call
         | ID -> var_node
         | array_access
         | "(" expression ")"

    function_call: ID "(" [arg_list] ")" -> call_node
    array_access: ID ("[" expression "]")+ -> array_access_node

    // --- TERMINALES ---
    VAR.2: /var/i
    MOD.2: "mod" | "MOD"
    DIV.2: "div" | "DIV"
    AND.2: /and/i
    OR.2: /or/i
    NOT.2: /not/i
    FOR.2: /for/i
    TO.2: /to/i
    DO.2: /do/i
    WHILE.2: /while/i
    IF.2: /if/i
    THEN.2: /then/i
    ELSE.2: /else/i
    BEGIN.2: /begin/i
    END.2: /end/i
    CALL.2: /call/i
    FUNCTION.2: /function/i

    STRING: /"[^"]*"/
    SEMICOLON: ";"
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
    
    COMMENT: /\/\/[^\n]*/
    %ignore SEMICOLON
    %import common.WS
    %ignore WS
    %ignore COMMENT
"""

@v_args(inline=True)
class AstTransformer(Transformer):
    def __init__(self):
        self.str = str
        self.int = int

    def _add_line(self, node, token):
        if hasattr(token, 'line'):
            node.line = token.line
        return node
    
    def start_node(self, *functions): return list(functions)
    
    def var_node(self, name):
        node = VarNode(name=str(name))
        return self._add_line(node, name)

    def const_node(self, value):
        return self._add_line(ConstNode(value=int(value)), value)
        
    def string_node(self, value):
        return self._add_line(ConstNode(value=str(value)[1:-1]), value)
        
    def array_access_node(self, name, *indices):
        return self._add_line(VarNode(name=f"{name}_multidim"), name)

    def unary_op(self, op, operand):
        return self._add_line(UnaryOpNode(op=str(op), operand=operand), op)

    def declaration_node(self, *items):
        seq = SequenceNode(statements=[ConstNode(value=1) for _ in items])
        if items and hasattr(items[0], 'line'): seq.line = items[0].line
        return seq

    def bin_op(self, *args):
        if len(args) == 1: return args[0]
        left = args[0]
        i = 1
        while i + 1 < len(args):
            op = args[i]
            right = args[i + 1]
            left = BinOpNode(left=left, op=str(op), right=right)
            if hasattr(op, 'line'): left.line = op.line
            elif hasattr(left, 'line'): pass
            i += 2
        return left

    def assign_node(self, target, assign_op, value):
        target_node = target if isinstance(target, VarNode) else VarNode(name=str(target))
        node = AssignNode(target=target_node, value=value)
        return self._add_line(node, assign_op)
    
    def sequence_node(self, *statements):
        flat = []
        for s in statements:
            if isinstance(s, list): flat.extend(s)
            elif isinstance(s, SequenceNode): flat.extend(s.statements)
            else: flat.append(s)
        return SequenceNode(statements=flat)

    def for_loop_node(self, var_id, assign_op, start, end, body):
        if not isinstance(body, SequenceNode): body = SequenceNode([body])
        node = ForLoopNode(variable=VarNode(str(var_id)), start=start, end=end, body=body)
        return self._add_line(node, var_id)

    def while_loop_node(self, cond, body):
        if not isinstance(body, SequenceNode): body = SequenceNode([body])
        node = WhileLoopNode(condition=cond, body=body)
        if hasattr(cond, 'line'): node.line = cond.line
        return node
    
    def if_node(self, cond, then_b, else_b=None):
        if not isinstance(then_b, SequenceNode): then_b = SequenceNode([then_b])
        if else_b and not isinstance(else_b, SequenceNode): else_b = SequenceNode([else_b])
        node = IfNode(condition=cond, then_branch=then_b, else_branch=else_b)
        if hasattr(cond, 'line'): node.line = cond.line
        return node

    def call_node(self, name, args=None):
        safe_args = args if args else []
        if hasattr(safe_args, 'children'): safe_args = safe_args.children
        node = CallNode(func_name=str(name), args=list(safe_args) if isinstance(safe_args, tuple) else safe_args)
        return self._add_line(node, name)
        
    def function_node(self, name, params, body):
        safe_params = params if params else []
        node = FunctionNode(name=str(name), params=list(safe_params), body=body)
        return self._add_line(node, name)

    def param_node(self, *args):
        valid_args = [arg for arg in args if arg is not None]
        if not valid_args: return VarNode(name="unknown")
        return VarNode(name=str(valid_args[-1]))

    def param_list(self, *params): return list(params)
    def arg_list(self, *args): return list(args)

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