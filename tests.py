TEST_CASES = [
    {
        "name": "1. Basico: IDs e Numeros (Anexo I)",
        "re_definitions": (
            "ID: [a-zA-Z_][a-zA-Z0-9_]*\n"
            "NUM: [0-9]+(\\.[0-9]+)?\n"
            "WS: [ ]+ %ignore" 
        ),
        "source_code": "var1 _var2 num123 3.14 0.5"
    },
    {
        "name": "2. Operadores e Palavras Chave",
        "re_definitions": (
            "IF: if\n"
            "ELSE: else\n"
            "WHILE: while\n"
            "ID: [a-zA-Z_][a-zA-Z0-9_]*\n"
            "NUM: [0-9]+\n"
            "ASSIGN: =\n"
            "PLUS: [+]\n"
            "MINUS: [-]\n"
            "MULTIPLY: [*]\n"
            "DIVIDE: [/]\n"
            "LPAREN: [(]\n"
            "RPAREN: [)]\n"
            "SEMICOLON: [;]\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "if x = 10; else y = 20; total = x + y * (z - 1);"
    },
    {
        "name": "3. Fechos Kleene (*, +, ?)",
        "re_definitions": (
            "A_STAR: a*\n"
            "B_PLUS: b+\n"
            "C_OPT: c?\n"
            "D_SEQ: d[ef]*g?h+\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "aaa bbb c dgg hh deeeefh d"
    },
    {
        "name": "4. Alternativas e Agrupamento",
        "re_definitions": (
            "ALT_GROUP: (ab|cd)+\n"
            "SIMPLE_ALT: x|y|z\n"
            "EMAIL_LIKE: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z][a-zA-Z][a-zA-Z]*\n" # Corrigido para teste original
            "WS: [ ]+ %ignore"
        ),
        "source_code": "ababcd x y z test@example.com another.test@sub.example.co.uk ab"
    },
    {
        "name": "5. Caso Vazio e Epsilon (se suportado)",
        "re_definitions": (
            "MAYBE_A: a?\n"
            "ID: b\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "b ab b" 
    },
    {
        "name": "6. Anexo I (ER1, ER2) & Anexo 3 Exemplo 2",
        "re_definitions": (
            "ER1: a?(a|b)+\n"
            "ER2: b?(a|b)+\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "aa bbbba ababab bbbbb c"
    },
    { 
        "name": "7. Estruturas de URL Simplificadas com Prioridade",
        "re_definitions": (
            "URL_FULL: (http|ftp)s?://[a-zA-Z0-9-]+(\\.[a-zA-Z0-9-]+)+(/([a-zA-Z0-9_.~-]+)?)*\n"
            "EMAIL: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z][a-zA-Z][a-zA-Z]*\n"  # Correção aqui
            "IDENT_GENERIC: [a-zA-Z_]+\n"
            "WS: [ ]+ %ignore" 
        ),
        "source_code": "http://example.com/path/to/doc.html https://sub-domain.another-example.org/ ftp://archive.example/a/b/c user.name@email-server.co.uk not_a_url_or_email"
    },
    {
        "name": "8. Opcional em Literal (dentro de token)",
        "re_definitions": (
            "TOKEN_LAP: la?p\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "lap lp l p"
    },
    { 
        "name": "9. Definições de Funções com Tipos e Identificadores",
        "re_definitions": (
            "KW_FUNCTION: function\n"
            "KW_VAR: var\n"
            "ID: [a-zA-Z_][a-zA-Z0-9_]*\n"
            "LPAREN: \\(\n"
            "RPAREN: \\)\n"
            "COMMA: ,\n"
            "COLON: :\n"
            "TYPE_HINT: int|string|float|bool|void\n"
            "ARROW: ->\n"
            "EQ: =\n"
            "NUMBER: [0-9]+\n"
            "SEMICOLON: ;\n"
            "WS: [ ]+ %ignore" 
        ),
        "source_code": "function process(id: int, name: string, value: float) -> void; var setup = function(); function simple(valid: bool): bool;"
    },
    {
        "name": "10. Alternância Agrupada com Repetição (+)",
        "re_definitions": (
            "PAT: (cat|dog)+\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "catdogcat dog dogcat catdog"
    },
    { 
        "name": "11. Expressões Aritméticas e Lógicas Combinadas",
        "re_definitions": (
            "LET: let\n"
            "CONST: const\n"
            "ID: [a-zA-Z_][a-zA-Z0-9_]*\n"
            "NUMBER: [0-9]+(\\.[0-9]+)?\n"
            "ASSIGN: =\n"
            "PLUS: \\+\n"
            "MINUS: -\n"
            "MULTIPLY: \\*\n"
            "DIVIDE: /\n"
            "MODULO: %\n"
            "LPAREN: \\(\n"
            "RPAREN: \\)\n"
            "SEMICOLON: ;\n"
            "EQ_COMP: ==\n"
            "NEQ_COMP: !=\n"
            "LT_COMP: <\n"
            "GT_COMP: >\n"
            "LTE_COMP: <=\n"
            "GTE_COMP: >=\n"
            "AND: and\n"
            "OR_LOGIC: \\|\\|\n"
            "NOT_LOGIC: !\n"
            "TRUE_KW: true\n"
            "FALSE_KW: false\n"
            "WS: [ ]+ %ignore" 
        ),
        "source_code": "let a = 10 * (2 + 3); const b = a % 7 >= 0.5; let result = (a > 5 and b == true) || !(a < 0); c = a / 2.0;"
    },
    {
        "name": "12. Classe de Caracteres (Ranges Simples) e Concatenação",
        "re_definitions": (
            "NUM_PART: [0-5]+\n"
            "ALPHA_PART: [A-C]+\n"
            "MIXED_ID: [a-c][0-9]\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "123 05 ABC CAB a0 b1 c2 678"
    },
    {
        "name": "13. Metacaracteres Escapados como Literais",
        "re_definitions": (
            "LIT_STAR: \\*\n"
            "LIT_PLUS: \\+\n"
            "LIT_Q: \\?\n"
            "LIT_PIPE: \\|\n"
            "LIT_DOT: \\.\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "* + ? | ."
    },
    {
        "name": "14. Ignorando Espaços e Múltiplas Definições Simples",
        "re_definitions": (
            "KW_FOR: for\n"
            "IDENT: [a-z]+\n"
            "SEMI: ;\n"
            "WS: [ ]+ %ignore" 
        ),
        "source_code": "for x ; for y ;"
    },
    {
        "name": "15. Prioridade de Definição (Prefixos)",
        "re_definitions": (
            "FORLOOP: forloop\n"
            "FOR: for\n"
            "LOOP: loop\n"
            "ID: [a-zA-Z]+\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "for forloop loop id"
    },
    {
        "name": "16. Grupo Opcional em Token Mais Longo",
        "re_definitions": (
            "USER_ID: user(-[0-9]+)?\n"
            "SEP: ::\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "user :: user-123 :: admin"
    },
    {
        "name": "17. Grupos Aninhados Simples com Operadores",
        "re_definitions": (
            "NESTED_TOKEN: a(b|c)*d\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "ad abcd acccbd axd abc"
    },
    {
        "name": "18. Concatenação com Opcional e Grupo Simples",
        "re_definitions": (
            "ITEM_OPC: item(-[abc])?\n"
            "NUM: [0-9]+\n"
            "WS: [ ]+ %ignore"
        ),
        "source_code": "item item-a 123 item-d item-b"
    }
]