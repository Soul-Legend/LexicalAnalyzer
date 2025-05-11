def parse_re_file_data(re_file_content):
    definitions = {} # pattern_name -> regex_string
    pattern_order = [] # To maintain order of definition for precedence
    reserved_words_defs = {} # lowercase_lexeme -> PATTERN_NAME (e.g. "if" -> "IF_TOKEN")

    for line_num, line in enumerate(re_file_content.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"): # Skip empty lines and comments
            continue
        
        if ':' not in line:
            print(f"Warning (line {line_num}): Skipping malformed line (no ':' found): {line}")
            continue
        
        name_part, regex_part = line.split(':', 1)
        name = name_part.strip()
        regex = regex_part.strip()

        if not name or not regex:
            print(f"Warning (line {line_num}): Skipping line with empty name or regex: {line}")
            continue
            
        definitions[name] = regex
        if name not in pattern_order:
            pattern_order.append(name)
        
        # Heuristic for reserved words: if NAME_IS_UPPER and regex_is_lower_and_matches_name
        # e.g., IF: if
        if name.isupper() and regex.islower() and name.lower() == regex:
            reserved_words_defs[regex] = name # Store as "if": "IF"
            
    return definitions, pattern_order, reserved_words_defs