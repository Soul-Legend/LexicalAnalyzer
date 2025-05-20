# lexer_core.py
class SymbolTable:
    def __init__(self):
        self.table = [] 
        self.lexeme_to_index = {} 

    def add_symbol(self, lexeme, token_type_base):
        if lexeme not in self.lexeme_to_index:
            index = len(self.table)
            entry = {"lexeme": lexeme, "token_type_base": token_type_base}
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
            return "Tabela de Símbolos vazia."
        header = f"{'Índice':<7} | {'Lexema':<20} | {'Tipo Base':<10}\n" + "-"*45
        rows = [header]
        for i, entry in enumerate(self.table):
            rows.append(f"{i:<7} | {entry['lexeme']:<20} | {entry['token_type_base']:<10}")
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

        if name.isupper() and regex.islower() and name.lower() == regex:
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
            last_match_pattern_name = None

            temp_read_pos = pos
            
            # Try to match as long as possible
            while temp_read_pos < source_len:
                char_to_read = source_code[temp_read_pos]
                
                # Check if current_dfa_state is an accept state BEFORE trying to transition
                if current_dfa_state in self.dfa.accept_states:
                    last_match_end_pos = temp_read_pos 
                    last_match_lexeme = source_code[start_pos_for_token : temp_read_pos]
                    last_match_pattern_name = self.dfa.accept_states[current_dfa_state]

                if (current_dfa_state, char_to_read) in self.dfa.transitions:
                    current_dfa_state = self.dfa.transitions[(current_dfa_state, char_to_read)]
                    temp_read_pos += 1
                else:
                    # Cannot transition further with this char_to_read
                    break
            
            # After the loop, check if the final state reached is an accept state
            if temp_read_pos > start_pos_for_token and current_dfa_state in self.dfa.accept_states:
                # This match is potentially longer than previous one if loop broke on valid transition
                last_match_end_pos = temp_read_pos
                last_match_lexeme = source_code[start_pos_for_token : temp_read_pos]
                last_match_pattern_name = self.dfa.accept_states[current_dfa_state]
            
            if last_match_pattern_name: # A valid token was found
                actual_token_type = last_match_pattern_name 
                attribute = last_match_lexeme

                if not last_match_lexeme and last_match_end_pos == start_pos_for_token:
                    if start_pos_for_token < source_len:
                        actual_failing_char = source_code[start_pos_for_token]
                        tokens_output_list.append((actual_failing_char, "ERRO!", actual_failing_char))
                        pos = start_pos_for_token + 1
                        continue
                
                if last_match_pattern_name in self.patterns_to_ignore:
                    pos = last_match_end_pos
                    continue

                if last_match_lexeme.lower() in self.reserved_words:
                    actual_token_type = self.reserved_words[last_match_lexeme.lower()]
                    attribute = None 

                if actual_token_type == "ID":
                    st_index = self.symbol_table.add_symbol(last_match_lexeme, "ID")
                    attribute = st_index 
                elif actual_token_type == "NUM": 
                    try:
                        attribute = float(last_match_lexeme) if '.' in last_match_lexeme else int(last_match_lexeme)
                    except ValueError:
                        attribute = last_match_lexeme 

                tokens_output_list.append((last_match_lexeme, actual_token_type, attribute))
                pos = last_match_end_pos 
            
            else: # No token could be formed starting at start_pos_for_token
                if start_pos_for_token < source_len:
                    actual_failing_char = source_code[start_pos_for_token]
                    tokens_output_list.append((actual_failing_char, "ERRO!", actual_failing_char))
                    pos += 1 
                else: # Should not happen if pos < source_len is the loop condition
                    break
        return tokens_output_list, self.symbol_table