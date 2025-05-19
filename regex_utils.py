# regex_utils.py
from config import EPSILON, CONCAT_OP

REGEX_META_OPERATORS = "*+?|."
REGEX_GROUPING_SYMBOLS = "()"

def is_literal_char(char_code):
    if char_code == EPSILON:
        return True
    return char_code not in REGEX_META_OPERATORS and char_code not in REGEX_GROUPING_SYMBOLS

def precedence(op):
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
    while i < len(content):
        if i + 2 < len(content) and content[i+1] == '-':
            start_char = content[i]
            end_char = content[i+2]
            is_alpha_range = start_char.isalpha() and end_char.isalpha()
            is_digit_range = start_char.isdigit() and end_char.isdigit()

            if (is_alpha_range or is_digit_range) and ord(start_char) <= ord(end_char):
                for char_code_val in range(ord(start_char), ord(end_char) + 1):
                    expanded_chars.append(chr(char_code_val))
                i += 3
            else:
                expanded_chars.append(content[i])
                i += 1
        else:
            expanded_chars.append(content[i])
            i += 1
    
    if not expanded_chars:
        return "" 
    if len(expanded_chars) == 1:
        return expanded_chars[0]
    
    return "(" + "|".join(expanded_chars) + ")"


def preprocess_regex(regex_str):
    current_regex = regex_str

    processed_re_pass1 = ""
    i = 0
    while i < len(current_regex):
        if current_regex[i] == '[':
            try:
                j = current_regex.find(']', i + 1)
                if j == -1: raise ValueError("Mismatched '[' in regex")
                char_class_segment = current_regex[i : j+1]
                expanded_segment = expand_char_class(char_class_segment)
                processed_re_pass1 += expanded_segment
                i = j + 1
            except ValueError as e:
                raise ValueError(f"Error processing char class '{current_regex[i:]}': {e}")
        else:
            processed_re_pass1 += current_regex[i]
            i += 1
    
    processed_re_pass2 = []
    if not processed_re_pass1: return ""

    idx = 0
    while idx < len(processed_re_pass1):
        char_k = processed_re_pass1[idx]
        processed_re_pass2.append(char_k)

        if idx < len(processed_re_pass1) - 1:
            next_char = processed_re_pass1[idx+1]
            
            char_k_can_end = is_literal_char(char_k) or char_k in (')', '*', '+', '?') 
            next_char_can_start = is_literal_char(next_char) or next_char == '('
            
            if char_k_can_end and next_char_can_start:
                processed_re_pass2.append(CONCAT_OP)
        idx += 1
        
    return "".join(processed_re_pass2)


def infix_to_postfix(infix_expr):
    if not infix_expr: return ""
    preprocessed_infix = preprocess_regex(infix_expr)
    if not preprocessed_infix: return ""

    postfix = []
    stack = []

    for char_code in preprocessed_infix:
        if is_literal_char(char_code):
            postfix.append(char_code)
        elif char_code == '(':
            stack.append(char_code)
        elif char_code == ')':
            while stack and stack[-1] != '(':
                postfix.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()
            else:
                raise ValueError(f"Mismatched parentheses in regex: '{infix_expr}' -> '{preprocessed_infix}'")
        elif char_code in ['*', CONCAT_OP, '|', '+', '?']: 
            while stack and stack[-1] != '(' and precedence(stack[-1]) >= precedence(char_code):
                postfix.append(stack.pop())
            stack.append(char_code)
        else:
            raise ValueError(f"Unknown character '{char_code}' in preprocessed regex '{preprocessed_infix}' (from '{infix_expr}')")
    
    while stack:
        if stack[-1] == '(':
            raise ValueError(f"Mismatched parentheses (remaining '(') in regex: '{infix_expr}' -> '{preprocessed_infix}'")
        postfix.append(stack.pop())
    return "".join(postfix)