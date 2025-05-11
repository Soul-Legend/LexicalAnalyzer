# lexer_core.py
"""
Core lexer functionality:
- Lexer class for tokenizing input string using a DFA.
- Parsing RE definition files.
"""

def parse_re_file_data(re_file_content):
    """
    Parses the content of an RE definition file.
    Returns:
        definitions (dict): pattern_name -> regex_string
        pattern_order (list): Order of pattern names for priority.
        reserved_words_defs (dict): lowercase_lexeme -> TOKEN_TYPE_NAME
        patterns_to_ignore (set): Set of pattern names to ignore in token output.
    """
    definitions = {}
    pattern_order = []
    reserved_words_defs = {}
    patterns_to_ignore = set()

    for line_num, line in enumerate(re_file_content.splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):  # Skip empty lines and comments
            continue
        
        directive_ignore = "%ignore"
        should_ignore = False
        if directive_ignore in line:
            line = line.replace(directive_ignore, "").strip() # Remove directive for parsing
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
        if name not in pattern_order: # Keep original order from file
            pattern_order.append(name)
        
        if should_ignore:
            patterns_to_ignore.add(name)

        # Heuristic for reserved words: if NAME is uppercase and regex is its lowercase version
        if name.isupper() and regex.islower() and name.lower() == regex:
            reserved_words_defs[regex] = name # e.g., "if" -> "IF"
            
    return definitions, pattern_order, reserved_words_defs, patterns_to_ignore


class Lexer:
    """Lexical analyzer that tokenizes input source code based on a DFA."""
    def __init__(self, dfa, reserved_words=None, patterns_to_ignore=None):
        self.dfa = dfa
        self.reserved_words = reserved_words if reserved_words else {}
        self.patterns_to_ignore = patterns_to_ignore if patterns_to_ignore else set()

    def tokenize(self, source_code):
        """Tokenizes the source code string."""
        tokens = []
        pos = 0
        source_len = len(source_code)

        while pos < source_len:
            current_dfa_state = self.dfa.start_state_id
            start_pos_for_token = pos # Where the current potential token begins
            
            last_match_end_pos = -1      # End position in source_code for the last accepted match
            last_match_lexeme = ""       # Lexeme of the last accepted match
            last_match_pattern_name = None # Pattern name of the last accepted match

            temp_read_pos = pos # Current reading head for maximal munch
            
            while temp_read_pos < source_len:
                char_to_read = source_code[temp_read_pos]
                
                if current_dfa_state in self.dfa.accept_states:
                    last_match_end_pos = temp_read_pos 
                    last_match_lexeme = source_code[start_pos_for_token : temp_read_pos]
                    last_match_pattern_name = self.dfa.accept_states[current_dfa_state]

                if (current_dfa_state, char_to_read) in self.dfa.transitions:
                    current_dfa_state = self.dfa.transitions[(current_dfa_state, char_to_read)]
                    temp_read_pos += 1
                else:
                    break # No transition for char_to_read
            
            # Check if the final state reached after consuming characters is an accept state
            if temp_read_pos > start_pos_for_token and current_dfa_state in self.dfa.accept_states:
                last_match_end_pos = temp_read_pos
                last_match_lexeme = source_code[start_pos_for_token : temp_read_pos]
                last_match_pattern_name = self.dfa.accept_states[current_dfa_state]
            
            # --- Process the longest valid match found ---
            if last_match_pattern_name:
                if last_match_pattern_name in self.patterns_to_ignore:
                    pos = last_match_end_pos # Consume ignored token's characters
                    continue # Skip adding to tokens list, move to next part of source

                final_lexeme = last_match_lexeme
                final_pattern = last_match_pattern_name

                # Check for reserved words
                # If lexeme (e.g. "if") is in reserved_words map (e.g. {"if": "IF_TOKEN"}), use that type.
                if final_lexeme.lower() in self.reserved_words:
                    final_pattern = self.reserved_words[final_lexeme.lower()]
                
                tokens.append((final_lexeme, final_pattern))
                pos = last_match_end_pos
            
            else: # No token matched starting at start_pos_for_token
                if start_pos_for_token < source_len: # Ensure not at EOF
                    # Lexical error: grab character or sequence for error message
                    error_lexeme_end = start_pos_for_token + 1
                    # Try to grab a "word" or until next whitespace for better error context
                    while error_lexeme_end < source_len and not source_code[error_lexeme_end].isspace():
                        error_lexeme_end += 1
                    
                    failing_lexeme = source_code[start_pos_for_token : error_lexeme_end]
                    if not failing_lexeme: # Should be at least one char if not EOF
                         failing_lexeme = source_code[start_pos_for_token]

                    tokens.append((failing_lexeme, "erro!"))
                    pos += len(failing_lexeme) # Advance past the erroneous segment
                else: # Should be EOF, loop will terminate
                    break
        return tokens