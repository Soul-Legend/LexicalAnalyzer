class Lexer:
    def __init__(self, dfa_instance, reserved_words=None):
        self.dfa = dfa_instance # Expects a fully constructed DFA object
        self.reserved_words = reserved_words if reserved_words else {} # lexeme.lower() -> TOKEN_TYPE

    def tokenize(self, source_code):
        tokens = []
        pos = 0
        source_len = len(source_code)

        while pos < source_len:
            # Skip whitespace
            start_pos_after_whitespace = pos
            while pos < source_len and source_code[pos].isspace():
                pos += 1
            
            if pos == source_len: # Reached end of source after skipping whitespace
                break
            
            current_dfa_state = self.dfa.start_state_id
            current_lexeme = ""
            
            last_accept_state_pos = -1
            last_accept_lexeme = ""
            last_accept_pattern = None

            temp_pos = pos 

            while temp_pos < source_len:
                char = source_code[temp_pos]
                
                # Check if current_dfa_state is an accept state BEFORE transitioning
                if current_dfa_state in self.dfa.accept_states:
                    last_accept_state_pos = temp_pos # Position *after* the char that formed current_lexeme
                    last_accept_lexeme = current_lexeme
                    last_accept_pattern = self.dfa.accept_states[current_dfa_state]

                # Try to transition
                if (current_dfa_state, char) in self.dfa.transitions:
                    current_dfa_state = self.dfa.transitions[(current_dfa_state, char)]
                    current_lexeme += char
                    temp_pos += 1
                else:
                    # No transition on this char from current_dfa_state
                    break 
            
            # After loop, check if the final state reached is an accept state
            if temp_pos == source_len or (current_dfa_state is not None and current_dfa_state in self.dfa.accept_states):
                 if current_dfa_state in self.dfa.accept_states: # Check one last time
                    last_accept_state_pos = temp_pos
                    last_accept_lexeme = current_lexeme
                    last_accept_pattern = self.dfa.accept_states[current_dfa_state]


            if last_accept_pattern: # Found a valid token
                final_lexeme = last_accept_lexeme
                final_pattern = last_accept_pattern

                # Check for reserved words
                if final_lexeme.lower() in self.reserved_words:
                    # Ensure the original pattern for the lexeme (e.g., ID) allows it to be a reserved word.
                    # This check might be more complex if, e.g., 'if' is a reserved word but also part of a longer ID 'ifdef'.
                    # For now, a simple lookup is fine as per typical lexer behavior.
                    final_pattern = self.reserved_words[final_lexeme.lower()]

                tokens.append((final_lexeme, final_pattern))
                pos = last_accept_state_pos # Advance main pointer
            else:
                # No valid token found starting at 'pos'
                # Report error: consume one char or until whitespace/next valid token
                failing_lexeme = ""
                error_scan_pos = pos
                
                # Consume until whitespace or known token boundary (more advanced)
                # For simplicity, consume non-whitespace characters
                while error_scan_pos < source_len and not source_code[error_scan_pos].isspace():
                    failing_lexeme += source_code[error_scan_pos]
                    error_scan_pos +=1
                
                if not failing_lexeme and pos < source_len: # If stuck on a single non-space char
                    failing_lexeme = source_code[pos]
                    pos += 1
                elif failing_lexeme:
                     pos += len(failing_lexeme)


                if failing_lexeme: # Ensure we actually consumed something for error
                    tokens.append((failing_lexeme, "erro!"))
                elif pos < source_len: # Should not happen if logic above is correct, but as a fallback
                    tokens.append((source_code[pos], "erro!"))
                    pos +=1
                # If failing_lexeme is empty and pos is at source_len, loop will naturally exit.
        return tokens