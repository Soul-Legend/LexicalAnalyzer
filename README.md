# AnalisadorLexico

Este projeto é um Gerador de Analisadores Léxicos desenvolvido como parte do Trabalho 1 da disciplina de Linguagens Formais e Compiladores. Ele permite que o usuário defina padrões de tokens usando expressões regulares, visualiza a construção dos autômatos finitos (NFA e DFA) e, finalmente, utiliza o analisador léxico gerado para tokenizar um código fonte de entrada.
    

## Funcionalidades Principais

Definição de Expressões Regulares (ERs): Permite a entrada de definições para diferentes tipos de tokens.

Dois Métodos de Construção de Autômatos:

    Thompson: ER → NFA (pós-fixa) → NFA Combinado → DFA (subconjuntos) → DFA Minimizado.

    Followpos (Árvore): ER → Árvore Sintática Aumentada → Cálculo de nullable, firstpos, lastpos, followpos → DFA Direto (não minimizado) → DFA Minimizado. (Nota: a implementação atual do Followpos para múltiplas ERs funciona melhor tratando cada ER individualmente para visualização detalhada, ou combinando-as em uma super-ER antes do processo para gerar um único DFA para o lexer).

Visualização de Etapas:

    Detalhes da construção (ERs pós-fixadas, árvores sintáticas, tabelas de followpos).

    NFAs individuais e o NFA combinado (para o método Thompson).

    DFAs não minimizados e minimizados (tabelas de transição).

    Desenho gráfico do AFD minimizado final (requer Graphviz instalado).

Tabela de Símbolos:

    Exibição das definições de padrões e palavras reservadas (estático).

    Exibição de uma tabela de símbolos dinâmica populada com identificadores encontrados durante a análise léxica do código fonte.

Geração de Tokens: Análise de um texto fonte fornecido para produzir uma lista de tokens no formato <lexema, TIPO_TOKEN> ou <TIPO_TOKEN, atributo_TS> para identificadores.

Modos de Operação:

    Modo Manual (Thompson): O usuário controla cada etapa da construção via algoritmo de Thompson.

    Modo Manual (Followpos): O usuário controla cada etapa da construção via algoritmo de Followpos (construção direta de DFA).

    Modo Automático (Testes): Permite carregar casos de teste pré-definidos que executam o fluxo completo via Thompson.

## Como Utilizar o Aplicativo
Python 3.x.
Instalar as bibliotecas:
pip install customtkinter       (Interface de usuario)
pip install Pillow              (Pega a imagem feita pelo graphviz e joga para a interface)
pip install Graphviz            (Permite desenha os automatos resultantes)

Se OS for windows abrir PowerShell como adiministrador e rodar:
choco install graphviz
Link do site: https://community.chocolatey.org/packages/Graphviz
Talvez seja necessario baixar o graphviz e rodar o executavel e colocar no path:
https://graphviz.org/download/

depois de baixar o graphviz e as bibliotecas é necessario fechar o editor de codigo e abrir novamente. 

Navegue até a pasta raiz do projeto (AnalisadorLexico/) e execute:
python main.py

### Tela inicial:
    Escolha o modo de operação:

    Modo Manual (Thompson): Para seguir o processo ER → NFA → DFA.

    Modo Manual (Followpos): Para seguir o processo ER → DFA Direto.

    Modo Automático (Testes): Para carregar exemplos pré-definidos.

### Interface Principal (Modo Manual): 

A interface é dividida em um painel de "Controles e Definições" à esquerda e um painel de "Visualização com Abas" à direita.

Painel de Controles e Definições:

    Definições Regulares:

        Digite ou carregue de um arquivo (.txt, .re) as definições dos seus tokens. O formato é NOME_DO_TOKEN: ExpressaoRegular.
        Comentários: Linhas iniciadas com # são ignoradas.
        Ignorando Tokens: Adicione %ignore ao final da linha de uma definição para que os lexemas correspondentes sejam consumidos da entrada, mas não gerem um token na saída final (útil para espaços em branco, comentários da linguagem fonte).
        Caracteres Literais: Um caractere normal representa ele mesmo. Ex: a, b, 1, _.
        Concatenação: Sequência de caracteres ou sub-expressões. Ex: abc (casa "abc"). O sistema insere operadores de concatenação implícitos onde necessário.
        Alternativa (OU): O operador |. Ex: a|b (casa "a" OU "b").
        Classes de Caracteres: [...] define um conjunto de caracteres aceitáveis.
                [abc] : Casa "a" OU "b" OU "c".
                [a-z] : Casa qualquer letra minúscula de "a" até "z".
                [A-Z] : Casa qualquer letra maiúscula de "A" até "Z".
                [0-9] : Casa qualquer dígito de "0" até "9".
                [a-zA-Z0-9_] : Casa qualquer letra (maiúscula ou minúscula), dígito ou underscore.
                Literais Dentro de Classes: A maioria dos metacaracteres de ER (como *, +, ?, (, )) perdem seu significado especial dentro de [] e são tratados como literais. Ex: [+*-] casa o caractere +, ou -, ou *.
                Escape Dentro de Classes: Use \ para escapar caracteres que ainda têm significado especial dentro de [], como \ em si ([\\]), ] ([\\]]), ou - se não estiver definindo um range ([a\\-z]).
        Agrupamento: Parênteses (...) agrupam sub-expressões para aplicar operadores ou definir precedência. Ex: (ab)+.
        Operadores de Repetição (Fechos):
            * (Fecho de Kleene): Zero ou mais ocorrências do item anterior. Ex: a* (casa "", "a", "aa", ...).
            + (Fecho Positivo): Uma ou mais ocorrências do item anterior. Ex: a+ (casa "a", "aa", ... mas não "").
            ? (Opcional): Zero ou uma ocorrência do item anterior. Ex: a? (casa "" ou "a").
        Caracteres Especiais e Escapes:
            Para usar um metacaractere de ER (como ., *, +, ?, |, (, )) como um caractere literal fora de uma classe de caracteres, você deve escapá-lo com uma barra invertida \. Ex: \. para o caractere ponto literal, \* para o caractere asterisco literal.

            O caractere & é reservado pelo sistema para representar a transição épsilon interna dos NFAs e não deve ser usado como um caractere literal nas suas ERs de entrada, a menos que você modifique config.py e toda a lógica associada. Se precisar do caractere '&' literal, use \&.

        Exemplos de Definições Regulares:

            Identificadores: ID: [a-zA-Z_][a-zA-Z0-9_]*

                Começa com letra ou underscore, seguido por zero ou mais letras, números ou underscores.

            Números Inteiros: NUM_INT: [0-9]+

                Um ou mais dígitos. Exemplos de lexemas: 1, 123, 0, 98765.

            Números Decimais (Ponto como Separador): NUM_DEC: [0-9]+(\.[0-9]+)?

                Um ou mais dígitos, opcionalmente seguidos por um ponto literal e mais um ou mais dígitos. Note o \. para escapar o ponto, tratando-o como um caractere literal. 123, 3.14, 0.5, 100.00. Note que também casa 123 porque a parte decimal é opcional. Se quisesse apenas números com ponto, removeria o ?.

            Palavras Reservadas: IF: if 
                                    ELSE: else    
                                    WHILE: while

                        Estas são definições literais. O sistema identifica automaticamente "if" como o lexema para o token IF (e similarmente para ELSE e WHILE) porque o nome do token está em maiúsculas e a ER é sua forma exata em minúsculas. Esses tokens terão prioridade sobre um ID genérico se o lexema for idêntico.

            Operadores:

                PLUS: [+] (O literal +)
                MINUS: [-]
                MULTIPLY: [*]
                ASSIGN: =
                LPAREN: [(]
                RPAREN: [)]

                Importante: Para usar caracteres que são metacaracteres de ER (como +, *, (, )) como literais, coloque-os dentro de classes de caracteres []. O sistema tentará interpretá-los como literais. Para o ponto . como literal, use \..

            Espaço em Branco (para ignorar): WS: [ ]+ %ignore

                Um ou mais espaços, tabs ou novas linhas. A diretiva %ignore faz com que os tokens correspondentes a este padrão não apareçam na saída final de tokens, mas sejam consumidos da entrada.

        Clique em "A. REs ➔ Autômatos Ind. / AFD Direto".

            Modo Thompson: Gera NFAs individuais para cada ER. Os detalhes (ER pós-fixada, NFA) são mostrados na aba "Construção Detalhada". O botão "B. Unir NFAs" é habilitado.

            Modo Followpos: Gera um AFD direto (não minimizado) para a primeira ER (para fins de detalhamento da árvore/followpos) e tenta gerar um AFD direto para a linguagem combinada (idealmente, (RE1)|(RE2)|...). Detalhes da árvore aumentada, tabela de followpos e o AFD direto de exemplo são mostrados na aba "Construção Detalhada". O AFD direto unificado (ou o da primeira RE) é mostrado em "Autômato Intermediário / União". O botão "C. Determinar/Minimizar" é habilitado.

    Etapa B (Apenas Modo Thompson):

        Clique em "B. Unir NFAs (Thompson)".

        Um NFA global é criado combinando os NFAs individuais com transições épsilon. É exibido na aba "Autômato Intermediário / União". O botão "C. Determinar/Minimizar" é habilitado.

        Esta etapa também executa a determinização (NFA → AFD não minimizado) e exibe este AFD na mesma aba.

    Etapa C (Minimização):

        Clique em "C. Determinar/Minimizar ➔ AFD Final".

        Modo Thompson: O AFD não minimizado (gerado na etapa B) é minimizado.

        Modo Followpos: O AFD direto (gerado na etapa A) é minimizado.

        Ambos os AFDs (não minimizado e minimizado final) são exibidos em formato de tabela na aba "AFD (Não Minimizado e Minimizado)".

        Os botões "Desenhar AFD Minimizado", "Salvar Tabela AFD" e "Analisar Texto Fonte" são habilitados.

    Desenhar AFD:

        Clique em "🎨 Desenhar AFD Minimizado".

        Uma imagem do AFD minimizado é gerada na pasta imagens/ e exibida na aba "Desenho AFD".

    Salvar AFD:

        Clique em "Salvar Tabela AFD Minimizada (Anexo II)".

        Permite salvar a tabela de transição do AFD minimizado no formato especificado pelo enunciado do trabalho, além de versões legíveis dos AFDs não minimizado e minimizado.

    Texto Fonte para Análise:

        Digite o código fonte que você deseja analisar na caixa de texto apropriada.

        Clique em "Analisar Texto Fonte (Gerar Tokens)".

        Os tokens reconhecidos são exibidos na aba "Tokens Gerados".

        A Tabela de Símbolos dinâmica (com identificadores encontrados) é populada e exibida na aba "Tabela de Símbolos".

Painel de Visualização com Abas:

    Construção Detalhada: Mostra detalhes da conversão ER para NFA (Thompson) ou da construção da Árvore Aumentada/Followpos (Followpos).

    Autômato Intermediário / União: Exibe o NFA combinado (Thompson) ou o AFD direto unificado (Followpos) antes da minimização final. Para Thompson, também mostra o AFD não minimizado resultante da determinização do NFA combinado.

    AFD (Não Minimizado e Minimizado): Apresenta as tabelas de transição do AFD antes e depois da minimização.

    Desenho AFD: Exibe a imagem gráfica do AFD minimizado.

    Tabela de Símbolos: Mostra as definições de padrões e palavras reservadas (após a Etapa A) e, após a análise de um texto fonte, a tabela de símbolos dinâmica com os identificadores encontrados.

    Tokens Gerados: Lista os tokens extraídos do texto fonte.

### Modo Automático (Testes):
    Seleciona um dos casos de teste pré-definidos.

As definições regulares e o código fonte do teste são carregados automaticamente.

O usuário pode então clicar nos botões de processamento (A, B, C) para ver o sistema em ação com o exemplo carregado (o fluxo é sempre via Thompson neste modo).

## Observações

Alfabeto e Escapes: Para usar caracteres especiais de ER (como . * + ? ( )) como literais em suas definições, coloque-os dentro de classes de caracteres (ex: PLUS: [+]) ou escape-os com uma barra invertida (ex: PONTO: \.). O caractere & é reservado para representar o épsilon interno dos NFAs e não deve ser usado como um caractere de entrada literal nas ERs, a menos que você modifique o config.py.

Prioridade de Padrões: A ordem em que as definições regulares são listadas no arquivo de entrada (ou na caixa de texto) determina sua prioridade. A primeira regra que corresponder a uma sequência de entrada será a escolhida (princípio da correspondência mais longa e, em caso de empate, a regra listada primeiro).

Erros Léxicos: Caracteres ou sequências não reconhecidas no texto fonte são reportados como <lexema, ERRO!>.