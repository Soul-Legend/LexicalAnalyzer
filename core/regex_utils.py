from .config import EPSILON, CONCAT_OP

REGEX_META_OPERATORS = "*+?|." 
REGEX_GROUPING_SYMBOLS = "()"
ALL_SPECIAL_REGEX_CHARS = REGEX_META_OPERATORS + REGEX_GROUPING_SYMBOLS

def is_literal_char(char_code):
    '''
    Verifica se o caracter não está na lista de caracteres especiais.
    Também retorna true se for epsilon.
    '''
    if char_code == EPSILON:
        return True
    return char_code not in ALL_SPECIAL_REGEX_CHARS

def precedence(op):
    '''
    Retorna precedencia dos operadores
    '''
    if op == '*' or op == '+' or op == '?':
        return 3
    if op == CONCAT_OP:
        return 2
    if op == '|':
        return 1
    return 0

def expand_char_class(char_class_str):
    content = char_class_str[1:-1]
    expanded_chars = []
    i = 0
    # Itera sobre toda a classe de caracteres
    while i < len(content):
        # Trata caracter precedido por \ como ele mesmo
        if content[i] == '\\' and i + 1 < len(content): 
            expanded_chars.append(content[i:i+2]) 
            i += 2
            continue
        # A partir classe de caracteres, gera a lista de caracteres
        # contida naquela classe
        # Ex: [a-c] -> [a, b, c]
        # Ex: [1-4] -> [1, 2, 3, 4]
        if i + 2 < len(content) and content[i+1] == '-':
            start_char_val = content[i]
            end_char_val = content[i+2]
            
            if len(start_char_val) == 1 and len(end_char_val) == 1: 
                is_alpha_range = start_char_val.isalpha() and end_char_val.isalpha()
                is_digit_range = start_char_val.isdigit() and end_char_val.isdigit()

                if (is_alpha_range or is_digit_range) and ord(start_char_val) <= ord(end_char_val):
                    for char_code_val in range(ord(start_char_val), ord(end_char_val) + 1):
                        char_to_add = chr(char_code_val)
                        if char_to_add in ALL_SPECIAL_REGEX_CHARS:
                            expanded_chars.append('\\' + char_to_add)
                        else:
                            expanded_chars.append(char_to_add)
                    i += 3
                    continue 
            
            expanded_chars.append(content[i]) 
            i += 1
        # Trata caracteres unitarios especiais e comuns
        else: 
            char_to_add = content[i]
            if char_to_add in ALL_SPECIAL_REGEX_CHARS:
                 expanded_chars.append('\\' + char_to_add)
            else:
                 expanded_chars.append(char_to_add)
            i += 1
            
    if not expanded_chars:
        return "" 
    
    if len(expanded_chars) == 1:
        return expanded_chars[0]
    
    # Retorna nova ER no formato expandido:
    # Ex: Dado a lista [a, b, c], retorna (a|b|c)
    return "(" + "|".join(expanded_chars) + ")"


def preprocess_regex(regex_str):
    '''
    Pré processa a ER 'regex_str'. Uma ER pré processada
    terá suas classes de caracteres expandidas e operações de
    concatenação serão adicionadas onde necessário.
    Ex: [a-c](ab)+c -> (a|b|c).(a.b)+.c
    '''
    current_regex = regex_str
    processed_re_pass1 = ""
    i = 0
    # Itera sobre toda a ER
    while i < len(current_regex):
        # Trata caracter precedido por barra como um caracter só
        # Ex: '\.' são tratados juntos
        if current_regex[i] == '\\':
            if i + 1 < len(current_regex):
                processed_re_pass1 += current_regex[i:i+2] 
                i += 2
            else:
                processed_re_pass1 += current_regex[i] 
                i += 1
        # Trata conjuntos de caracteres
        # Ex: [a-z]
        elif current_regex[i] == '[':
            try:
                j = i + 1
                bracket_level = 1 
                
                search_idx = i + 1
                end_bracket_idx = -1
                # Procura pelo ']'
                while search_idx < len(current_regex):
                    if current_regex[search_idx] == ']' and (search_idx == 0 or current_regex[search_idx-1] != '\\'):
                        end_bracket_idx = search_idx
                        break
                    search_idx +=1

                # Se não achou, acusa erro
                if end_bracket_idx == -1: raise ValueError("Mismatched '[' in regex")
                
                # Se achou, expande classe de caracteres
                # Ex: [a-z] -> (a|b|c|...|z)
                char_class_segment = current_regex[i : end_bracket_idx+1]
                expanded_segment = expand_char_class(char_class_segment)
                processed_re_pass1 += expanded_segment
                i = end_bracket_idx + 1
            except ValueError as e:
                raise ValueError(f"Error processing char class '{current_regex[i:]}': {e}")
        else:
            processed_re_pass1 += current_regex[i]
            i += 1
    
    # Itera sobre a string da ER expandida e guarda cada
    # caracter numa lista
    tokens_for_concat = []
    k = 0
    while k < len(processed_re_pass1):
        char = processed_re_pass1[k]
        if char == '\\':
            if k + 1 < len(processed_re_pass1):
                tokens_for_concat.append(processed_re_pass1[k:k+2])
                k += 2
            else:
                tokens_for_concat.append(char)
                k += 1
        else:
            tokens_for_concat.append(char)
            k += 1
    
    final_tokens_with_concat = []
    if not tokens_for_concat: return ""

    # Adiciona a operação de concateção entre expressoes de uma ER
    # Ex: (a|b)c -> (a|b).c
    for idx, token_k in enumerate(tokens_for_concat):
        final_tokens_with_concat.append(token_k)

        if idx < len(tokens_for_concat) - 1:
            next_token_peek = tokens_for_concat[idx+1]
            
            # Retorna true se o caracter pode finalizar uma ER
            def can_end_operand(tk):
                if len(tk) == 2 and tk.startswith('\\'): return True
                if len(tk) == 1: return is_literal_char(tk) or tk in (')', '*', '+', '?')
                return False 

            # Retorna true se o caracter pode iniciar uma ER
            def can_start_operand(tk):
                if len(tk) == 2 and tk.startswith('\\'): return True
                if len(tk) == 1: return is_literal_char(tk) or tk == '('
                return False

            if can_end_operand(token_k) and can_start_operand(next_token_peek):
                final_tokens_with_concat.append(CONCAT_OP)

    return "".join(final_tokens_with_concat)


def is_token_literal(token_str): 
    if len(token_str) == 2 and token_str.startswith('\\'):
        return True
    if token_str == EPSILON:
        return True
    if len(token_str) == 1:
        return is_literal_char(token_str) 
    return False

def infix_to_postfix(infix_expr):
    '''
    Pré processa e transforma a ER em sua representação pós fixa
    Ex: [a-c](ab)+c -> (a|b|c).(a.b)+.c -> ab|c|ab.+.c.
    '''
    if not infix_expr: return [] 
    
    preprocessed_infix_str = preprocess_regex(infix_expr)
    if not preprocessed_infix_str: return []

    # Itera sobre a ER pre processada e adiciona cada caracter
    # a uma lista
    tokens = []
    i = 0
    while i < len(preprocessed_infix_str):
        char = preprocessed_infix_str[i]
        if char == '\\':
            if i + 1 < len(preprocessed_infix_str):
                tokens.append(preprocessed_infix_str[i:i+2])
                i += 2
            else:
                tokens.append(char) 
                i += 1
        elif char in ['*', CONCAT_OP, '|', '+', '?', '(', ')']:
            tokens.append(char)
            i += 1
        else: 
            tokens.append(char)
            i += 1
    
    postfix_tokens = []
    stack = [] 

    for token in tokens:
        # Se for um literal, adiciona a lista que representa
        # a expressão pós fixa
        if is_token_literal(token):
            postfix_tokens.append(token)
        # Se for um (, empilha
        elif token == '(':
            stack.append(token)
        # Se for um ), desempilha o (
        elif token == ')':
            while stack and stack[-1] != '(':
                postfix_tokens.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()
            else:
                raise ValueError(f"Mismatched parentheses in regex: '{infix_expr}' -> '{preprocessed_infix_str}'")
        # Se for um operador
        elif token in ['*', CONCAT_OP, '|', '+', '?']: 
            while stack and stack[-1] != '(' and precedence(stack[-1]) >= precedence(token):
                postfix_tokens.append(stack.pop())
            stack.append(token)
        else:
            raise ValueError(f"Unknown token '{token}' during postfix conversion from '{infix_expr}'")
    
    while stack:
        if stack[-1] == '(':
            raise ValueError(f"Mismatched parentheses (remaining '(') in regex: '{infix_expr}' -> '{preprocessed_infix_str}'")
        postfix_tokens.append(stack.pop())
    
    return postfix_tokens