class SymbolTable:
    def __init__(self):
        self.table = []
        self.lexeme_to_index = {}

    def add_symbol(self, lexeme, token_type):
        """
        Adds a lexeme and its token type to the symbol table.
        If the lexeme already exists, its existing index is returned.
        Assumes the lexer resolves a lexeme to a single definitive token_type.
        """
        if lexeme not in self.lexeme_to_index:
            index = len(self.table)
            entry = {"lexeme": lexeme, "token_type": token_type}
            self.table.append(entry)
            self.lexeme_to_index[lexeme] = index
            return index
        return self.lexeme_to_index[lexeme]

    def get_symbol_entry(self, index):
        if 0 <= index < len(self.table):
            return self.table[index]
        return None

    def get_index(self, lexeme):
        return self.lexeme_to_index.get(lexeme)

    def clear(self):
        self.table.clear()
        self.lexeme_to_index.clear()

    def __str__(self):
        if not self.table:
            return "Tabela de Símbolos (Dinâmica) vazia."
        header = f"{'Índice':<7} | {'Lexema':<20} | {'Tipo':<15}\n" + "-"*47
        rows = [header]
        for i, entry in enumerate(self.table):
            rows.append(f"{i:<7} | {entry['lexeme']:<20} | {entry['token_type']:<15}")
        return "\n".join(rows)


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

        is_likely_reserved = name.isupper() and name.lower() == regex
        if is_likely_reserved:
            reserved_words_defs[regex] = name

    return definitions, pattern_order, reserved_words_defs, patterns_to_ignore


class Lexer:
    def __init__(self, dfa, reserved_words=None, patterns_to_ignore=None, symbol_table_instance=None):
        self.dfa = dfa
        self.reserved_words = reserved_words if reserved_words else {}
        self.patterns_to_ignore = patterns_to_ignore if patterns_to_ignore else set()
        self.symbol_table = symbol_table_instance if symbol_table_instance else SymbolTable()

    def tokenize(self, source_code):
        self.symbol_table.clear()
        tokens_output_list = []

        pos = 0
        source_len = len(source_code)

        while pos < source_len:
            current_dfa_state = self.dfa.start_state_id
            start_pos_for_token = pos

            last_match_end_pos = -1
            last_match_lexeme = ""
            base_pattern_name_from_dfa = None

            temp_read_pos = pos

            # Consome entrada e avança sobre os estados do automato
            # Quando chega a um estado de aceitação, anota que passou por ele
            while temp_read_pos < source_len:
                char_to_read = source_code[temp_read_pos]

                if current_dfa_state in self.dfa.accept_states:
                    last_match_end_pos = temp_read_pos
                    last_match_lexeme = source_code[start_pos_for_token : temp_read_pos]
                    base_pattern_name_from_dfa = self.dfa.accept_states[current_dfa_state]

                if (current_dfa_state, char_to_read) in self.dfa.transitions:
                    current_dfa_state = self.dfa.transitions[(current_dfa_state, char_to_read)]
                    temp_read_pos += 1
                else:
                    break
            
            if temp_read_pos > start_pos_for_token and current_dfa_state in self.dfa.accept_states:
                last_match_end_pos = temp_read_pos
                last_match_lexeme = source_code[start_pos_for_token : temp_read_pos]
                base_pattern_name_from_dfa = self.dfa.accept_states[current_dfa_state]
            
            # Se chegou num estado de aceitação
            if base_pattern_name_from_dfa:
                # Se é um token vazio, acusa erro
                if not last_match_lexeme and last_match_end_pos == start_pos_for_token:
                    if base_pattern_name_from_dfa not in self.patterns_to_ignore:
                        error_char_display = source_code[start_pos_for_token : start_pos_for_token+1] if start_pos_for_token < source_len else "<EOF>"
                        tokens_output_list.append((error_char_display, "ERRO!", f"Zero-length match by {base_pattern_name_from_dfa} at pos {start_pos_for_token}"))
                        pos = start_pos_for_token + 1
                        continue

                # Se é um padrão a ser ignorado, ignora
                if base_pattern_name_from_dfa in self.patterns_to_ignore:
                    pos = last_match_end_pos
                    if last_match_end_pos == start_pos_for_token:
                        pos +=1
                    continue

                final_token_type = base_pattern_name_from_dfa
                
                # --- INÍCIO DA MODIFICAÇÃO PARA O TRABALHO 2 ---
                # A lógica do atributo do token agora depende do tipo.
                is_reserved = last_match_lexeme.lower() in self.reserved_words
                final_attribute = None

                # Adiciona à tabela de símbolos primeiro para obter o índice
                symbol_index = self.symbol_table.add_symbol(last_match_lexeme, final_token_type)

                if is_reserved:
                    # O tipo do token é o da palavra reservada, atributo é nulo
                    final_token_type = self.reserved_words[last_match_lexeme.lower()]
                    final_attribute = None
                elif final_token_type == "ID":
                    # O atributo para ID é seu índice na tabela de símbolos
                    final_attribute = symbol_index
                elif final_token_type == "NUM":
                    # O atributo para NUM é seu valor numérico
                    try:
                        final_attribute = float(last_match_lexeme) if '.' in last_match_lexeme else int(last_match_lexeme)
                    except ValueError:
                        final_attribute = last_match_lexeme # Fallback
                else:
                    # Para outros literais, o atributo pode ser o próprio lexema ou nulo
                    final_attribute = last_match_lexeme

                tokens_output_list.append((last_match_lexeme, final_token_type, final_attribute))
                # --- FIM DA MODIFICAÇÃO ---

                pos = last_match_end_pos
            # Se não chegou num estado de aceitação, anota que aconteceu um erro e continua análise
            else:
                if start_pos_for_token < source_len:
                    actual_failing_char = source_code[start_pos_for_token]
                    tokens_output_list.append((actual_failing_char, "ERRO!", actual_failing_char))
                    pos += 1
                else: 
                    break
        return tokens_output_list, self.symbol_table