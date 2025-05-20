TEST_CASES = [
    {
        "name": "Basico: IDs e Numeros (Anexo I)",
        "re_definitions": (
            "ID: [a-zA-Z_][a-zA-Z0-9_]*\n"
            "NUM: [0-9]+(\.[0-9]+)?\n" # Adicionado suporte a decimal com \.
            "WS: [ ]+ %ignore" 
        ),
        "source_code": "var1 _var2 num123 3.14 0.5"
    },
    {
        "name": "Operadores e Palavras Chave",
        "re_definitions": (
            "IF: if\n"
            "ELSE: else\n"
            "WHILE: while\n"
            "ID: [a-zA-Z_][a-zA-Z0-9_]*\n"
            "NUM: [0-9]+\n"
            "ASSIGN: =\n"
            "PLUS: [+]\n" # Usando classe de caractere para literais
            "MINUS: [-]\n"
            "MULTIPLY: [*]\n"
            "DIVIDE: [/]\n"
            "LPAREN: [(]\n"
            "RPAREN: [)]\n"
            "SEMICOLON: [;]\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": (
            "if x = 10; "
            "else y = 20; "
            "total = x + y * (z - 1);"
        )
    },
    {
        "name": "Fechos Kleene (*, +, ?)",
        "re_definitions": (
            "A_STAR: a*\n"
            "B_PLUS: b+\n"
            "C_OPT: c?\n"
            "D_SEQ: d[ef]*g?h+\n" # Sequência com todos os fechos
            "WS: [ ]+ %ignore"
        ),
        "source_code": "aaa bbb c dgg hh deeeefh d"
    },
    {
        "name": "Alternativas e Agrupamento",
        "re_definitions": (
            "ALT_GROUP: (ab|cd)+\n"
            "SIMPLE_ALT: x|y|z\n"
            # Simplified EMAIL_LIKE: replaced {2,} with [a-zA-Z][a-zA-Z]+
            "EMAIL_LIKE: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z][a-zA-Z]+\n" 
            "WS: [ ]+ %ignore"
        ),
        "source_code": "ababcd x y z test@example.com another.test@sub.example.co.uk ab"
    },
     {
        "name": "Classes de Caracteres Complexas e Escapes",
        "re_definitions": (
            "ID: [a-zA-Z]+\n" 
            "PUNCT: [.,!?;:]\n"
            "SPECIALS_IN_CLASS: [+\\-*/%&|^<=>()[\\]{}] %ignore\n"
            "ESCAPED_DOT: \\.\n" 
            "ESCAPED_STAR: \\*\n" 
            "STRING: \"([a-z]|\\\\.)*\"\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "Hello, world! Test: specials +-*/%&|^<=>()[]{} . * \"astringwith\\\"escapes\\\"andbs\\\\.\""
    },
    {
        "name": "Caso Vazio e Epsilon (se suportado)",
        "re_definitions": (
            "MAYBE_A: a?\n"
            "ALWAYS_EPSILON: &\n" # Se & for para epsilon literal
            "ID: b\n"
             "WS: [ ]+ %ignore"
        ),
        "source_code": "b ab b" # '&' como entrada literal não é o mesmo que token epsilon
                               # Se ALWAYS_EPSILON: & for interpretado como string vazia, o lexer atual não a emite como token.
    },
    {
        "name": "Anexo I (ER1, ER2) & Anexo 3 Exemplo 2",
        "re_definitions": (
            "ER1: a?(a|b)+\n"
            "ER2: b?(a|b)+\n"
            "WS: ( )+ %ignore"
        ),
        "source_code": (
            "aa "
            "bbbba "
            "ababab "
            "bbbbb "
            "c" 
        )
    }
]