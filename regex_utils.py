# regex_utils.py
from config import EPSILON, CONCAT_OP

REGEX_META_OPERATORS = "*+?|."
REGEX_GROUPING_SYMBOLS = "()"

class RegexSyntaxTreeNode:
    def __init__(self, value, node_type, left=None, right=None):
        self.value = value
        self.type = node_type # 'literal', 'concat', 'union', 'star', 'plus', 'optional'
        self.left = left
        self.right = right

    def __repr__(self, level=0, prefix="Root:"):
        ret = "\t" * level + prefix + f"({self.type}, {self.value})\n"
        if self.left:
            ret += self.left.__repr__(level + 1, "L---")
        if self.right:
            ret += self.right.__repr__(level + 1, "R---")
        return ret

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
    processed_re_pass1 = ""
    i = 0
    while i < len(regex_str):
        if regex_str[i] == '[':
            try:
                j = regex_str.index(']', i + 1)
                char_class_segment = regex_str[i : j+1]
                expanded_segment = expand_char_class(char_class_segment)
                processed_re_pass1 += expanded_segment
                i = j + 1
            except ValueError:
                processed_re_pass1 += regex_str[i]
                i += 1
        else:
            processed_re_pass1 += regex_str[i]
            i += 1
    
    processed_re_pass2 = []
    if not processed_re_pass1: return ""

    for k, char_k in enumerate(processed_re_pass1):
        processed_re_pass2.append(char_k)
        if k < len(processed_re_pass1) - 1:
            next_char = processed_re_pass1[k+1]
            char_k_ends_operand_construct = is_literal_char(char_k) or char_k in (')', '*', '+', '?')
            next_char_starts_operand_construct = is_literal_char(next_char) or next_char == '('
            if char_k_ends_operand_construct and next_char_starts_operand_construct:
                processed_re_pass2.append(CONCAT_OP)
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
        elif char_code in REGEX_META_OPERATORS:
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

def infix_to_syntax_tree(infix_expr):
    if not infix_expr: return None
    preprocessed_infix = preprocess_regex(infix_expr)
    if not preprocessed_infix: return None

    operand_stack = [] # Stores RegexSyntaxTreeNode objects
    operator_stack = []

    def apply_op():
        op = operator_stack.pop()
        if op == '*' or op == '+' or op == '?':
            if not operand_stack: raise ValueError(f"Not enough operands for unary operator {op}")
            right = operand_stack.pop()
            node_type = {'*': 'star', '+': 'plus', '?': 'optional'}[op]
            operand_stack.append(RegexSyntaxTreeNode(op, node_type, left=right))
        elif op == CONCAT_OP or op == '|':
            if len(operand_stack) < 2: raise ValueError(f"Not enough operands for binary operator {op}")
            right = operand_stack.pop()
            left = operand_stack.pop()
            node_type = {CONCAT_OP: 'concat', '|': 'union'}[op]
            operand_stack.append(RegexSyntaxTreeNode(op, node_type, left=left, right=right))

    for char_code in preprocessed_infix:
        if is_literal_char(char_code):
            operand_stack.append(RegexSyntaxTreeNode(char_code, 'literal'))
        elif char_code == '(':
            operator_stack.append(char_code)
        elif char_code == ')':
            while operator_stack and operator_stack[-1] != '(':
                apply_op()
            if operator_stack and operator_stack[-1] == '(':
                operator_stack.pop() # Pop '('
            else:
                raise ValueError(f"Mismatched parentheses in regex: '{infix_expr}' -> '{preprocessed_infix}' for tree")
        elif char_code in REGEX_META_OPERATORS:
            while operator_stack and operator_stack[-1] != '(' and \
                  precedence(operator_stack[-1]) >= precedence(char_code):
                apply_op()
            operator_stack.append(char_code)
        else:
            raise ValueError(f"Unknown character '{char_code}' in preprocessed regex '{preprocessed_infix}' for tree")

    while operator_stack:
        if operator_stack[-1] == '(':
            raise ValueError(f"Mismatched parentheses (remaining '(') in regex: '{infix_expr}' -> '{preprocessed_infix}' for tree")
        apply_op()

    if len(operand_stack) != 1:
        raise ValueError(f"Invalid expression for tree construction, final stack size: {len(operand_stack)}")
    return operand_stack[0]