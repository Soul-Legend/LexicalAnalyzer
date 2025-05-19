# lexer_core.py

def parse_re_file_data(re_file_content):
    definitions = {}
    pattern_order = []
    reserved_words_defs = {}
    patterns_to_ignore = set()

    for line_num, line in enumerate(re_file_content.splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        directive_ignore = "%ignore"
        should_ignore = False
        if directive_ignore in line:
            line = line.replace(directive_ignore, "").strip()
            should_ignore = True

        if ':' not in line:
            print(f"Warning: Malformed line {line_num+1} (no ':'): '{line}'. Skipping.")
            continue
        
        name_part, regex_part = line.split(':', 1)
        name = name_part.strip()
        regex = regex_part.strip()

        if not name or not regex:
            print(f"Warning: Malformed line {line_num+1} (empty name or regex after split): '{line}'. Skipping.")
            continue

        if name in definitions:
            print(f"Warning: Duplicate definition for '{name}' on line {line_num+1}. Overwriting previous.")

        definitions[name] = regex
        if name not in pattern_order:
            pattern_order.append(name)
        
        if should_ignore:
            patterns_to_ignore.add(name)

        if name.isupper() and regex.islower() and name.lower() == regex:
            reserved_words_defs[regex] = name
            
    return definitions, pattern_order, reserved_words_defs, patterns_to_ignore


class Lexer:
    def __init__(self, dfa, reserved_words=None, patterns_to_ignore=None):
        self.dfa = dfa
        self.reserved_words = reserved_words if reserved_words else {}
        self.patterns_to_ignore = patterns_to_ignore if patterns_to_ignore else set()

    def tokenize(self, source_code):
        tokens = []
        pos = 0
        source_len = len(source_code)

        while pos < source_len:
            current_dfa_state = self.dfa.start_state_id
            start_pos_for_token = pos
            
            last_match_end_pos = -1
            last_match_lexeme = ""
            last_match_pattern_name = None

            temp_read_pos = pos
            
            # Verifica se o estado inicial já é um estado de aceitação (para linguagens que aceitam epsilon)
            # Esta lógica é para o caso de um padrão poder corresponder à string vazia no início da análise
            # ou entre tokens válidos.
            if self.dfa.start_state_id is not None and self.dfa.start_state_id in self.dfa.accept_states:
                 # Se o estado inicial é de aceitação, temos uma correspondência de comprimento zero.
                 # Isso é relevante se a ER pode ser epsilon.
                 # No entanto, um lexer geralmente avança consumindo caracteres.
                 # Lidar com "tokens epsilon" no meio de uma string é complexo e geralmente não é feito.
                 # Se uma ER como "a?" está no início e a string é "b", "a?" não consome 'a',
                 # mas não gera um token epsilon antes de tentar 'b'.
                 # Esta verificação aqui é mais para o caso de *toda* a string de entrada ser processada
                 # e o estado final ser de aceitação, ou para ERs que *apenas* aceitam epsilon.
                 # Para a tokenização progressiva, a lógica abaixo é mais relevante.
                 pass


            while temp_read_pos < source_len:
                char_to_read = source_code[temp_read_pos]
                
                # Se o caractere não estiver no alfabeto do DFA, ele não pode ser processado.
                # Isso pode ser um erro léxico, a menos que seja um espaço em branco ignorado
                # ou parte de um token mais longo que será tratado por `last_match_pattern_name`.
                if char_to_read not in self.dfa.alphabet and (current_dfa_state, char_to_read) not in self.dfa.transitions:
                    # Se já tínhamos uma correspondência válida, use-a.
                    # Se não, este caractere não pode iniciar uma nova transição válida a partir do estado atual.
                    break 


                if current_dfa_state in self.dfa.accept_states:
                    last_match_end_pos = temp_read_pos 
                    last_match_lexeme = source_code[start_pos_for_token : temp_read_pos]
                    last_match_pattern_name = self.dfa.accept_states[current_dfa_state]

                if (current_dfa_state, char_to_read) in self.dfa.transitions:
                    current_dfa_state = self.dfa.transitions[(current_dfa_state, char_to_read)]
                    temp_read_pos += 1
                else:
                    break
            
            if temp_read_pos > start_pos_for_token and current_dfa_state in self.dfa.accept_states:
                last_match_end_pos = temp_read_pos
                last_match_lexeme = source_code[start_pos_for_token : temp_read_pos]
                last_match_pattern_name = self.dfa.accept_states[current_dfa_state]
            
            if last_match_pattern_name:
                if last_match_pattern_name in self.patterns_to_ignore:
                    pos = last_match_end_pos
                    continue

                final_lexeme = last_match_lexeme
                final_pattern = last_match_pattern_name

                if final_lexeme.lower() in self.reserved_words:
                    final_pattern = self.reserved_words[final_lexeme.lower()]
                
                tokens.append((final_lexeme, final_pattern))
                pos = last_match_end_pos
            
            else:
                if start_pos_for_token < source_len:
                    error_lexeme_end = start_pos_for_token + 1
                    
                    # Tenta consumir até o próximo espaço em branco ou fim da linha para o erro
                    # Isso é apenas para dar um contexto melhor ao erro, não afeta o avanço.
                    # O avanço real será de um caractere se nenhum token for encontrado.
                    temp_error_context_end = error_lexeme_end
                    while temp_error_context_end < source_len and not source_code[temp_error_context_end].isspace():
                        temp_error_context_end +=1
                    
                    failing_lexeme_context = source_code[start_pos_for_token : temp_error_context_end]
                    
                    # O token de erro real é apenas o primeiro caractere não reconhecido
                    actual_failing_char = source_code[start_pos_for_token]

                    tokens.append((actual_failing_char, "erro!")) # Reporta apenas o primeiro char como erro
                    pos += 1 # Avança apenas um caractere
                else:
                    break
        return tokens