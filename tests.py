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
            r"WS: ( )+ %ignore"
        ),
        "source_code": (
            "a1 "
            "0 "
            "teste2 "
            "21 "
            "alpha123 "
            "3444 "
            "a43teste "
        )
    },
    {
        "name": "Anexo 1 (ER1, ER2) & Anexo 3 Exemplo 2",
        "re_definitions": (
            "ER1: a?(a|b)+\n"
            "ER2: b?(a|b)+\n"
            r"WS: ( )+ %ignore"
        ),
        "source_code": (
            "aa "
            "bbbba "
            "ababab "
            "bbbbb "
            "c" # Error case
        )
    },
    {
        "name": "Operadores Matemáticos Simples",
        "re_definitions": (
            "NUM: [0-9]+(\.[0-9]+)?\n"
            "PLUS: [+]\n"
            "EQ: [=]\n"
            "MINUS: [-]\n"
            "MUL: [*]\n"
            "DIV: [/]\n"
            "LPAREN: [(]\n"
            "RPAREN: [)]\n"
            "ID: [a-zA-Z_][a-zA-Z0-9_]*\n"
            r"WS: ( )+ %ignore"
        ),
        "source_code": (
            "var1 = ( 10 + 5.5 ) * 2 / x "
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
            r"WS: ( )+ %ignore"
        ),
        "source_code": (
            "if x = 10; // assign x "
            "else "
            "  /* block comment "
            "     y = 20; "
            "  */ "
            "  y = 20; "
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
            r"WS: ( )+ %ignore"
        ),
        "source_code": (
            "hello \"world\\\"!\" 'a' 'b\\'' "
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
            r"WS: ( )+ %ignore"
        ),
        "source_code": (
            "b "      # A_STAR_B, A_OPT_B
            "ab "     # A_STAR_B, A_PLUS_B, A_OPT_B
            "aaab "   # A_STAR_B, A_PLUS_B
            "cdcdc "  # C_OR_D_STAR
            "e"        # Error
        )
    }
]