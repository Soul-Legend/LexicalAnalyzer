SYNTACTIC_TEST_CASES = [
    {
        "name": "Teste 1: Gramática Mínima",
        "grammar": "S ::= x",
        "token_stream": "x,"
    },
    {
        "name": "Teste 2: Produção com Épsilon",
        "grammar": "A ::= x A\nA ::= &",
        "token_stream": ""
    },
    {
        "name": "Teste 3: Expressões (Precedência)",
        "grammar": (
            "E ::= E + T\n"
            "E ::= T\n"
            "T ::= T * F\n"
            "T ::= F\n"
            "F ::= id"
        ),
        "token_stream": "id,0\n*,\nid,1\n+,\nid,2"
    },
    {
        "name": "Teste 4: Aninhamento e Recursão",
        "grammar": "S ::= ( S )\nS ::= &",
        "token_stream": "(\n(\n)\n)"
    },
    {
        "name": "Teste 5: Palavras Reservadas",
        "grammar": (
            "S ::= if E then S\n"
            "S ::= id\n"
            "E ::= id"
        ),
        "token_stream": "if,\nid,0\nthen,\nid,1"
    },
    {
        "name": "Teste 6: Produção Longa",
        "grammar": (
            "S ::= let id = E ;\n"
            "E ::= id"
        ),
        "token_stream": "let,\nid,0\n=,\nid,1\n;,"
    },
    {
        "name": "Teste 7: Anuláveis em Cascata",
        "grammar": (
            "S ::= A B C d\n"
            "A ::= a | &\n"
            "B ::= b | &\n"
            "C ::= c | &"
        ),
        "token_stream": "a,\nc,\nd,"
    },
    {
        "name": "Teste 8: Lista com Recursão à Direita",
        "grammar": (
            "L ::= id R\n"
            "R ::= , L\n"
            "R ::= &"
        ),
        "token_stream": "id,0\n,\nid,1\n,\nid,2"
    },
    {
        "name": "Teste 9: Sentença Complexa (Precedência e Parênteses)",
        "grammar": (
            "E ::= E + T\n"
            "E ::= T\n"
            "T ::= T * F\n"
            "T ::= F\n"
            "F ::= ( E )\n"
            "F ::= id"
        ),
        "token_stream": "(\nid,0\n+,\nid,1\n)\n*,\nid,2"
    },
    {
        "name": "Teste 10: Lista com Recursão à Esquerda",
        "grammar": (
            "SList ::= SList S\n"
            "SList ::= S\n"
            "S ::= id ;"
        ),
        "token_stream": "id,0\n;,\nid,1\n;,"
    },
    {
        "name": "Teste 11: Operador Unário",
        "grammar": (
            "E ::= E + T\n"
            "E ::= T\n"
            "T ::= - T\n"
            "T ::= F\n"
            "F ::= id"
        ),
        "token_stream": "-,\nid,0\n+,\nid,1"
    },
    {
        "name": "Teste 12: Estrutura de Bloco",
        "grammar": (
            "S ::= begin SList end\n"
            "SList ::= S ; SList\n"
            "SList ::= S\n"
            "S ::= a"
        ),
        "token_stream": "begin,\na,\n;,\na,\nend,"
    },
    {
        "name": "Teste 13: Gramática com Associatividade à Direita",
        "grammar": (
            "S ::= E\n"
            "E ::= T + E\n"
            "E ::= T\n"
            "T ::= id"
        ),
        "token_stream": "id,0\n+,\nid,1\n+,\nid,2"
    }
]