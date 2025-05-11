# tests.py
"""
Stores test cases for the Lexer Generator.
Each test case is a dictionary with 'name', 're_definitions', and 'source_code'.
"""

TEST_CASES = [
    {
        "name": "Anexo 1 (ID, NUM) & Anexo 3 Exemplo 1",
        "re_definitions": (
            "ID: [a-zA-Z]([a-zA-Z]|[0-9])*\n"
            "NUM: [1-9]([0-9])*|0\n"
            "WS: ( |\t|\r|\n)+ %ignore"
        ),
        "source_code": (
            "a1\n"
            "0\n"
            "teste2\n"
            "21\n"
            "alpha123\n"
            "3444\n"
            "a43teste"
        )
    },
    {
        "name": "Anexo 1 (ER1, ER2) & Anexo 3 Exemplo 2",
        "re_definitions": (
            "ER1: a?(a|b)+\n"
            "ER2: b?(a|b)+\n"
            "WS: ( |\t|\r|\n)+ %ignore"
        ),
        "source_code": (
            "aa\n"
            "bbbba\n"
            "ababab\n"
            "bbbbb\n"
            "c" # Error case
        )
    },
    {
        "name": "Operadores Matemáticos Simples",
        "re_definitions": (
            "NUM: [0-9]+([.][0-9]+)?\n"
            "PLUS: [+]\n"
            "MINUS: [-]\n"
            "MUL: [*]\n"
            "DIV: [/]\n"
            "LPAREN: [(]\n"
            "RPAREN: [)]\n"
            "ID: [a-zA-Z_][a-zA-Z0-9_]*\n"
            "WS: [ \t\r\n]+ %ignore"
        ),
        "source_code": (
            "var1 = (10 + 5.5) * 2 / x\n"
            "3 - 1"
        )
    },
    {
        "name": "Palavras Reservadas e Comentários",
        "re_definitions": (
            "IF: if\n"
            "ELSE: else\n"
            "WHILE: while\n"
            "ID: [a-zA-Z_][a-zA-Z0-9_]*\n"
            "NUM: [0-9]+\n"
            "ASSIGN: =\n"
            "SEMI: ;\n"
            "COMMENT_LINE: //([^\r\n])*\n" # %ignore not specified here, so it becomes a token
            "COMMENT_BLOCK: /*(.|[\r\n])*?*/ %ignore\n" # This complex one might need careful NFA construction
            "WS: [ \t\r\n]+ %ignore"
        ),
        "source_code": (
            "if x = 10; // assign x\n"
            "else\n"
            "  /* block comment\n"
            "     y = 20;\n"
            "  */\n"
            "  y = 20;\n"
            "while z;"
        )
    },
    {
        "name": "Strings e Caracteres Especiais",
        "re_definitions": (
            "STRING_DQ: \"([^\"\\\\]|\\\\.)*\"\n" # Double quoted string with escapes
            "CHAR_SQ: '([^'\\\\]|\\\\.)'\n"   # Single quoted char with escapes
            "ID: [a-z]+\n"
            "PUNCT: [.,!?;]\n"
            "WS: [ \t\r\n]+ %ignore"
        ),
        "source_code": (
            "hello \"world\\\"!\" 'a' 'b\\''\n"
            "test, punct!"
        )
    },
    {
        "name": "Regex com Fechos e Opcional",
        "re_definitions": (
            "A_STAR_B: a*b\n"
            "A_PLUS_B: a+b\n"
            "A_OPT_B: a?b\n"
            "C_OR_D_STAR: (c|d)*\n"
            "WS: [ \t\r\n]+ %ignore"
        ),
        "source_code": (
            "b\n"      # A_STAR_B, A_OPT_B
            "ab\n"     # A_STAR_B, A_PLUS_B, A_OPT_B
            "aaab\n"   # A_STAR_B, A_PLUS_B
            "cdcdc\n"  # C_OR_D_STAR
            "e"        # Error
        )
    }
]