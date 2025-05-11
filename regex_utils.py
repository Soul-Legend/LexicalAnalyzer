# regex_utils.py
"""
Utilities for processing regular expressions:
- Character class expansion
- Preprocessing (e.g., adding explicit concatenation)
- Infix to postfix conversion
"""
from config import EPSILON, CONCAT_OP

# These are characters that have special meaning in the regex syntax itself (operators, grouping)
# The CONCAT_OP is added during preprocessing, so it's also a meta operator.
REGEX_META_OPERATORS = "*+?|."  # Includes CONCAT_OP
REGEX_GROUPING_SYMBOLS = "()"

def is_literal_char(char_code):
    """
    Determines if a character in a regex string should be treated as a literal
    for an NFA transition, rather than a regex meta-operator or grouping symbol.
    Epsilon is a special literal.
    """
    if char_code == EPSILON:
        return True
    return char_code not in REGEX_META_OPERATORS and char_code not in REGEX_GROUPING_SYMBOLS

def precedence(op):
    """Returns the precedence of a regex operator."""
    if op == '*' or op == '+' or op == '?':
        return 3
    if op == CONCAT_OP: # Concatenation
        return 2
    if op == '|': # Alternation
        return 1
    return 0 # Default for others (should not happen for known operators)

def expand_char_class(char_class_str):
    """
    Expands a character class string like "[a-zA-Z0-9]" into an OR-ed regex string.
    Example: "[a-c0-1]" -> "(a|b|c|0|1)"
    Example: "[+*-]" -> "(+|-|*)" (order might vary but content is ORed)
    Example: "[a]" -> "a"
    """
    content = char_class_str[1:-1]  # Remove [ and ]
    expanded_chars = []
    i = 0
    while i < len(content):
        # Check for range like a-z
        if i + 2 < len(content) and content[i+1] == '-':
            start_char = content[i]
            end_char = content[i+2]
            is_alpha_range = start_char.isalpha() and end_char.isalpha()
            is_digit_range = start_char.isdigit() and end_char.isdigit()

            if (is_alpha_range or is_digit_range) and ord(start_char) <= ord(end_char):
                for char_code_val in range(ord(start_char), ord(end_char) + 1):
                    expanded_chars.append(chr(char_code_val))
                i += 3  # Consumed 'x-y'
            else: # Not a valid range or malformed (e.g., z-a, a--, [-a]), treat start_char literally
                expanded_chars.append(content[i]) # Treat '-' as literal if not part of valid range start
                i += 1
        else:  # Single character
            expanded_chars.append(content[i])
            i += 1
    
    if not expanded_chars:
        return "" 
    if len(expanded_chars) == 1:
        # If the single char is a meta char or parenthesis, it should remain as is for later processing.
        # e.g. [+] should expand to just +, which is_literal_char will catch.
        # e.g. [(] should expand to just (, which is_literal_char will NOT catch (it's grouping).
        # This part is subtle. expand_char_class should produce literals or parenthesized groups of literals.
        # A single char from a class like '[+]' is just '+'.
        return expanded_chars[0]
    # For multiple expanded chars, group them with | and parentheses
    return "(" + "|".join(expanded_chars) + ")"

def preprocess_regex(regex_str):
    """
    Preprocesses a regex string:
    1. Expands character classes (e.g., [a-z]).
    2. Adds explicit concatenation operators ('.').
    """
    # Pass 1: Expand character classes
    processed_re_pass1 = ""
    i = 0
    while i < len(regex_str):
        if regex_str[i] == '[':
            try:
                # Find the matching ']'
                # This simple scan assumes non-nested, non-escaped brackets for char classes.
                j = regex_str.index(']', i + 1)
                char_class_segment = regex_str[i : j+1]
                expanded_segment = expand_char_class(char_class_segment)
                processed_re_pass1 += expanded_segment
                i = j + 1
            except ValueError: # No matching ']' or other issue
                processed_re_pass1 += regex_str[i] # Treat '[' literally or handle error
                i += 1
        else:
            processed_re_pass1 += regex_str[i]
            i += 1
    
    # Pass 2: Add explicit concatenation operators
    processed_re_pass2 = []
    if not processed_re_pass1: return ""

    for k, char_k in enumerate(processed_re_pass1):
        processed_re_pass2.append(char_k)
        if k < len(processed_re_pass1) - 1:
            next_char = processed_re_pass1[k+1]
            
            # char_k can be followed by an operand if it's a literal, or ), *, +, ?
            char_k_ends_operand_construct = is_literal_char(char_k) or char_k in (')', '*', '+', '?')
            # next_char can start an operand if it's a literal, or (
            next_char_starts_operand_construct = is_literal_char(next_char) or next_char == '('
            
            if char_k_ends_operand_construct and next_char_starts_operand_construct:
                processed_re_pass2.append(CONCAT_OP)
    return "".join(processed_re_pass2)

def infix_to_postfix(infix_expr):
    """Converts an infix regex string to postfix using shunting-yard."""
    if not infix_expr: return ""
    preprocessed_infix = preprocess_regex(infix_expr)
    if not preprocessed_infix: return "" # Handles cases where regex becomes empty after preprocessing

    postfix = []
    stack = [] # Operator stack

    for char_code in preprocessed_infix:
        if is_literal_char(char_code):
            postfix.append(char_code)
        elif char_code == '(':
            stack.append(char_code)
        elif char_code == ')':
            while stack and stack[-1] != '(':
                postfix.append(stack.pop())
            if stack and stack[-1] == '(': # Pop the '('
                stack.pop()
            else: # Mismatched parentheses
                raise ValueError(f"Mismatched parentheses in regex: '{infix_expr}' -> '{preprocessed_infix}'")
        elif char_code in REGEX_META_OPERATORS: # Operator
            while stack and stack[-1] != '(' and precedence(stack[-1]) >= precedence(char_code):
                postfix.append(stack.pop())
            stack.append(char_code)
        else:
            # This should not be reached if is_literal_char and REGEX_META_OPERATORS cover all cases from preprocess_regex
            raise ValueError(f"Unknown character '{char_code}' in preprocessed regex '{preprocessed_infix}' (from '{infix_expr}')")
    
    while stack: # Pop remaining operators
        if stack[-1] == '(':
            raise ValueError(f"Mismatched parentheses (remaining '(') in regex: '{infix_expr}' -> '{preprocessed_infix}'")
        postfix.append(stack.pop())
    return "".join(postfix)