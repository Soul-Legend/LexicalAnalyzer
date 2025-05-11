EPSILON = '&'
CONCAT_OP = '.'

def is_operand(char):
    return char.isalnum() or char == EPSILON

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
            if start_char.isalpha() and end_char.isalpha():
                for char_code in range(ord(start_char), ord(end_char) + 1):
                    expanded_chars.append(chr(char_code))
            elif start_char.isdigit() and end_char.isdigit():
                 for char_code in range(ord(start_char), ord(end_char) + 1):
                    expanded_chars.append(chr(char_code))
            else: # Handle cases like [a-], [-z] or invalid ranges as literals
                expanded_chars.append(start_char)
                if i+1 < len(content): expanded_chars.append(content[i+1])
                if i+2 < len(content): expanded_chars.append(content[i+2])

            i += 3
        else:
            expanded_chars.append(content[i])
            i += 1
    if not expanded_chars:
        return ""
    return "(" + "|".join(expanded_chars) + ")"

def preprocess_regex(regex_str):
    processed_re = ""
    i = 0
    while i < len(regex_str):
        if regex_str[i] == '[':
            j = i
            # Correctly find the matching ']' for char class
            balance = 0
            in_escape = False
            while j < len(regex_str):
                if regex_str[j] == '\\' and not in_escape:
                    in_escape = True
                    j += 1
                    continue
                if regex_str[j] == '[' and not in_escape:
                    balance += 1
                elif regex_str[j] == ']' and not in_escape:
                    balance -= 1
                    if balance == 0:
                        break
                in_escape = False
                j += 1

            if j < len(regex_str) and regex_str[j] == ']' and balance == 0 :
                char_class = regex_str[i:j+1]
                processed_re += expand_char_class(char_class)
                i = j + 1
            else: # Non-terminated or malformed char class, treat '[' literally
                processed_re += regex_str[i]
                i += 1
        else:
            processed_re += regex_str[i]
            i += 1
    
    regex_str = processed_re
    
    output = []
    for i, char in enumerate(regex_str):
        output.append(char)
        if i < len(regex_str) - 1:
            next_char = regex_str[i+1]
            # Ensure EPSILON is treated as an operand for concatenation
            is_current_operand_like = is_operand(char) or char in [')', '*', '+', '?']
            is_next_operand_like = is_operand(next_char) or next_char == '('
            
            if is_current_operand_like and is_next_operand_like:
                output.append(CONCAT_OP)
    return "".join(output)

def infix_to_postfix(infix_expr):
    preprocessed_infix = preprocess_regex(infix_expr)
    postfix = []
    stack = []
    for char in preprocessed_infix:
        if is_operand(char):
            postfix.append(char)
        elif char == '(':
            stack.append(char)
        elif char == ')':
            while stack and stack[-1] != '(':
                postfix.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop() 
            else:
                # This case implies mismatched parentheses before this point,
                # but preprocess_regex or other logic might not raise it.
                # Or, it could be an empty () which is not typical in basic regex.
                # For robustness, if stack is empty, it's an error.
                if not stack:
                     raise ValueError("Mismatched parentheses: Unmatched ')'")
        else: # Operator
            while stack and stack[-1] != '(' and precedence(stack[-1]) >= precedence(char):
                postfix.append(stack.pop())
            stack.append(char)
    
    while stack:
        if stack[-1] == '(':
            raise ValueError("Mismatched parentheses: Unmatched '('")
        postfix.append(stack.pop())
    return "".join(postfix)