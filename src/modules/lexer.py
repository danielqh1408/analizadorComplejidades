'''

"""
Módulo Lexer (Tokenizer) para el Analizador de Complejidades.

Este módulo es responsable de tomar una cadena de pseudocódigo
y descomponerla en una lista de Tokens. Utiliza un enfoque de 
expresión regular compilada única para alta eficiencia.
"""

import regex  # Usamos 'regex' (regex==2024.9.11) por su mejor soporte Unicode
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class Token:
    """
    Representa un token individual identificado por el Lexer.
    Es inmutable para mayor seguridad.
    """
    type: str     # Tipo de token (e.g., 'FOR', 'ID', 'NUMBER')
    value: object   # Valor del token (e.g., 'for', 'myVar', 123)
    line: int       # Número de línea donde se encontró
    column: int     # Número de columna donde comienza

class Lexer:
    """
    Implementa el analizador léxico.
    
    Propósito: Convertir una cadena de texto en una lista de Tokens.
    Algoritmo: 
        1. Define todas las especificaciones de tokens (regex) en una lista.
        2. Combina todas las especificaciones en una única expresión regular maestra.
        3. Compila la regex maestra (con flags UNICODE e IGNORECASE).
        4. Itera sobre la cadena de entrada usando finditer().
        5. Para cada coincidencia, identifica el tipo de token (grupo nombrado).
        6. Omite SKIP, COMMENT y NEWLINE.
        7. Genera un Token para todas las demás coincidencias.
        8. Lanza un SyntaxError si encuentra un MISMATCH.
    Complejidad: O(N), donde N es la longitud del código de entrada.
    Justificación: 
        - Eficiencia: Un solo `finditer` en una regex compilada es extremadamente rápido.
        - Mantenibilidad: Los tokens se definen declarativamente en `token_specs`.
        - Compatibilidad: Cumple con la gramática y el stack (Python 3.11, regex).
    """

    def __init__(self):
        """
        Inicializa el Lexer y compila la expresión regular maestra.
        """
        
        # Especificaciones de token [Tipo, Patrón Regex]
        # El orden es crucial: de más específico a más general.
        self.token_specs = [
            # 1. Ignorar
            ('COMMENT',   r'►[^\n]*'),        # Comentarios
            ('NEWLINE',   r'\n'),            # Saltos de línea
            ('SKIP',      r'[ \t]+'),        # Espacios y tabs

            # 2. Palabras clave (case-insensitive)
            ('FOR',       r'\bfor\b'),
            ('TO',        r'\bto\b'),
            ('DO',        r'\bdo\b'),
            ('WHILE',     r'\bwhile\b'),
            ('REPEAT',    r'\brepeat\b'),
            ('UNTIL',     r'\buntil\b'),
            ('IF',        r'\bif\b'),
            ('THEN',      r'\bthen\b'),
            ('ELSE',      r'\belse\b'),
            ('BEGIN',     r'\bbegin\b'),
            ('END',       r'\bend\b'),
            ('CALL',      r'\bcall\b'),        #
            ('RETURN',    r'\breturn\b'),      # Añadido para funciones

            # 3. Operadores y Palabras clave de operador (case-insensitive)
            ('ASSIGN',    r'🡨'),            #
            ('LTE',       r'≤'),            #
            ('GTE',       r'≥'),            #
            ('NEQ',       r'≠'),            #
            ('DIV_INT',   r'\bdiv\b'),        #
            ('MOD',       r'\bmod\b'),        #
            ('AND',       r'\band\b'),        #
            ('OR',        r'\bor\b'),         #
            ('NOT',       r'\bnot\b'),        #

            # 4. Operadores de un solo caracter
            ('EQ',        r'='),            #
            ('LT',        r'<'),            #
            ('GT',        r'>'),            #
            ('PLUS',      r'\+'),           #
            ('MINUS',     r'-'),           #
            ('TIMES',     r'\*'),           #
            ('DIV',       r'/'),           #

            # 5. Literales
            ('NUMBER',    r'\d+(\.\d*)?|\.\d+'), # Enteros y flotantes
            ('ID',        r'[a-zA-Z_][a-zA-Z0-9_]*'), # Identificadores

            # 6. Puntuación
            ('LPAREN',    r'\('),
            ('RPAREN',    r'\)'),
            ('LBRACKET',  r'\['),            #
            ('RBRACKET',  r'\]'),            #
            ('COMMA',     r','),
            ('DOT',       r'\.'),            #

            # 7. Error: debe ser el último
            ('MISMATCH',  r'.'),
        ]

        # Combinar todas las especificaciones en una regex maestra
        parts = [f'(?P<{name}>{pattern})' for name, pattern in self.token_specs]
        self.master_regex = regex.compile(
            '|'.join(parts), 
            regex.UNICODE | regex.IGNORECASE
        )
        
        # Tokens que deben ser normalizados a mayúsculas
        self.keyword_tokens = {
            'FOR', 'TO', 'DO', 'WHILE', 'REPEAT', 'UNTIL', 'IF', 'THEN', 
            'ELSE', 'BEGIN', 'END', 'CALL', 'RETURN', 
            'DIV_INT', 'MOD', 'AND', 'OR', 'NOT'
        }

    def tokenize(self, code: str) -> List[Token]:
        """
        Analiza una cadena de pseudocódigo y devuelve una lista de Tokens.
        
        Inputs:
            code (str): El código fuente a tokenizar.
        
        Outputs:
            List[Token]: La lista de tokens generada.
            
        Raises:
            SyntaxError: Si se encuentra un carácter ilegal (MISMATCH).
        """
        tokens: List[Token] = []
        line_num: int = 1
        line_start: int = 0

        # Iterar sobre todas las coincidencias en el texto
        for match in self.master_regex.finditer(code):
            kind = match.lastgroup  # El 'name' del grupo que coincidió
            value = match.group()
            column = match.start() - line_start + 1

            if kind == 'NEWLINE':
                line_num += 1
                line_start = match.end()
            elif kind == 'SKIP':
                pass  # Ignorar espacios en blanco
            elif kind == 'COMMENT':
                pass  # Ignorar comentarios
            elif kind == 'MISMATCH':
                raise SyntaxError(
                    f"Caracter ilegal '{value}' en línea {line_num}, col {column}"
                )
            else:
                # Normalizar valores
                if kind == 'NUMBER':
                    value = float(value) if '.' in value else int(value)
                elif kind in self.keyword_tokens:
                    # Normalizamos palabras clave a MAYÚSCLUS
                    value = value.upper() 
                
                tokens.append(Token(kind, value, line_num, column))
        
        # Añadir un token de fin de archivo (End-Of-File)
        tokens.append(Token('EOF', '', line_num, 0))
        return tokens

# --- Bloque de demostración ejecutable ---
# Se puede ejecutar con: python src/modules/lexer.py

if __name__ == "__main__":
    
    print("--- 🚀 Iniciando Demo del Lexer ---")
    
    # 1. Código de prueba
    test_code = """
    ► Algoritmo de prueba
    Algoritmo_Ejemplo(A[1..n])
    begin
        i 🡨 1
        WHILE (i < n) and (A[i] ≠ 99) do
        begin
            i 🡨 i + 1
        end
    end
    """

    print(f"Código a analizar:\n{test_code}")
    
    # 2. Tokenización
    lexer = Lexer()
    try:
        tokens = lexer.tokenize(test_code)
        
        print("--- ✅ Tokens Generados ---")
        for token in tokens:
            print(token)
            
    except SyntaxError as e:
        print(f"--- ❌ Error de Sintaxis ---")
        print(e)

    # 3. Ejemplo de error
    print("\n--- 🚀 Probando Error de Sintaxis ---")
    error_code = "x 🡨 (y + §)"
    
    print(f"Código a analizar: {error_code}\n")
    try:
        lexer.tokenize(error_code)
    except SyntaxError as e:
        print("--- ✅ Error Capturado Correctamente ---")
        print(f"Error: {e}")
"""
'''