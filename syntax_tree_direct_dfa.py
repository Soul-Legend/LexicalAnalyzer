from automata import DFA
from config import EPSILON, CONCAT_OP

LITERAL_NODE = 'literal'
CONCAT_NODE = 'concat'
UNION_NODE = 'union'
STAR_NODE = 'star'
PLUS_NODE = 'plus'
EPSILON_NODE = 'epsilon_literal'


class PositionNode:
    _id_counter = 1
    def __init__(self, symbol):
        self.symbol = symbol
        self.id = PositionNode._id_counter
        PositionNode._id_counter += 1
        self.followpos = set()

    def __repr__(self):
        return f"Pos({self.id},'{self.symbol}')"
    
    def __lt__(self, other):
        if isinstance(other, PositionNode):
            return self.id < other.id
        return NotImplemented
    
    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, PositionNode) and self.id == other.id

    @staticmethod
    def reset_id_counter():
        PositionNode._id_counter = 1

class AugmentedRegexSyntaxTreeNode:
    def __init__(self, value, node_type, left=None, right=None):
        self.value = value
        self.type = node_type
        self.left = left
        self.right = right
        self.nullable = False
        self.firstpos = set()
        self.lastpos = set()
        self.position_node = None

    def __repr__(self, level=0, prefix="Root:"):
        ret = "\t" * level + prefix + f"({self.type}, {self.value}, N:{self.nullable}, "
        ret += f"F:{ {p.id for p in self.firstpos} if self.firstpos else '{}' }, "
        ret += f"L:{ {p.id for p in self.lastpos} if self.lastpos else '{}' })\n"
        if self.position_node:
            ret += "\t" * (level+1) + f"PosNode: {self.position_node}\n"
        if self.left:
            ret += self.left.__repr__(level + 1, "L---")
        if self.right:
            ret += self.right.__repr__(level + 1, "R---")
        return ret

def build_augmented_syntax_tree(infix_expr, position_nodes_map):
    from regex_utils import preprocess_regex, precedence, is_literal_char as is_simple_literal
    
    END_MARKER_SYMBOL = '#' 
    
    processed_original_re = preprocess_regex(infix_expr)
    if not processed_original_re:
        end_marker_pos_node = PositionNode(END_MARKER_SYMBOL)
        position_nodes_map[end_marker_pos_node.id] = end_marker_pos_node
        end_marker_tree_node = AugmentedRegexSyntaxTreeNode(END_MARKER_SYMBOL, LITERAL_NODE)
        end_marker_tree_node.position_node = end_marker_pos_node
        return end_marker_tree_node, END_MARKER_SYMBOL


    operand_stack = [] 
    operator_stack = []

    def apply_pending_ops(current_op_precedence=0):
        while operator_stack and operator_stack[-1] != '(' and \
              precedence(operator_stack[-1]) >= current_op_precedence:
            op_char = operator_stack.pop()
            
            if op_char == '*':
                if not operand_stack: raise ValueError(f"Not enough operands for *")
                child = operand_stack.pop()
                operand_stack.append(AugmentedRegexSyntaxTreeNode(op_char, STAR_NODE, left=child))
            elif op_char == '+': 
                if not operand_stack: raise ValueError(f"Not enough operands for +")
                child = operand_stack.pop()
                operand_stack.append(AugmentedRegexSyntaxTreeNode(op_char, PLUS_NODE, left=child))
            elif op_char == '?':
                if not operand_stack: raise ValueError(f"Not enough operands for ?")
                child_R = operand_stack.pop()
                epsilon_node_for_q = AugmentedRegexSyntaxTreeNode(EPSILON, EPSILON_NODE)
                union_node = AugmentedRegexSyntaxTreeNode('|', UNION_NODE, left=child_R, right=epsilon_node_for_q)
                operand_stack.append(union_node)
            elif op_char == CONCAT_OP or op_char == '|':
                if len(operand_stack) < 2: raise ValueError(f"Not enough operands for {op_char}")
                right = operand_stack.pop()
                left = operand_stack.pop()
                node_type = CONCAT_NODE if op_char == CONCAT_OP else UNION_NODE
                operand_stack.append(AugmentedRegexSyntaxTreeNode(op_char, node_type, left=left, right=right))

    re_tokens = []
    temp_i = 0
    while temp_i < len(processed_original_re):
        char = processed_original_re[temp_i]
        if char == '\\':
            if temp_i + 1 < len(processed_original_re):
                re_tokens.append(processed_original_re[temp_i:temp_i+2])
                temp_i += 2
            else:
                re_tokens.append(char)
                temp_i += 1
        else:
            re_tokens.append(char)
            temp_i += 1

    for token_char_code in re_tokens:
        if is_simple_literal(token_char_code) and token_char_code != EPSILON :
            actual_symbol = token_char_code[1] if len(token_char_code) == 2 and token_char_code.startswith('\\') else token_char_code
            pos_node = PositionNode(actual_symbol)
            position_nodes_map[pos_node.id] = pos_node
            node = AugmentedRegexSyntaxTreeNode(actual_symbol, LITERAL_NODE)
            node.position_node = pos_node
            operand_stack.append(node)
        elif token_char_code == '(':
            operator_stack.append(token_char_code)
        elif token_char_code == ')':
            apply_pending_ops(0) 
            if not operator_stack or operator_stack[-1] != '(':
                raise ValueError(f"Mismatched parentheses for augmented tree: {processed_original_re}")
            operator_stack.pop() 
        elif token_char_code in ['*', CONCAT_OP, '|', '?', '+']: 
            apply_pending_ops(precedence(token_char_code))
            operator_stack.append(token_char_code)
        else: 
            raise ValueError(f"Unknown token '{token_char_code}' in preprocessed regex for augmented tree: {processed_original_re}")

    apply_pending_ops(0) 

    if len(operand_stack) != 1:
        raise ValueError(f"Invalid expression for augmented tree. Final operand stack size: {len(operand_stack)}")
    
    re_tree_root = operand_stack[0]
    
    end_marker_pos_node = PositionNode(END_MARKER_SYMBOL)
    position_nodes_map[end_marker_pos_node.id] = end_marker_pos_node
    end_marker_tree_node = AugmentedRegexSyntaxTreeNode(END_MARKER_SYMBOL, LITERAL_NODE)
    end_marker_tree_node.position_node = end_marker_pos_node

    final_root = AugmentedRegexSyntaxTreeNode(CONCAT_OP, CONCAT_NODE, left=re_tree_root, right=end_marker_tree_node)
    
    return final_root, END_MARKER_SYMBOL


def compute_functions(node):
    if node is None: return

    compute_functions(node.left)
    compute_functions(node.right)

    if node.type == LITERAL_NODE:
        node.nullable = False
        node.firstpos = {node.position_node}
        node.lastpos = {node.position_node}
    elif node.type == EPSILON_NODE:
        node.nullable = True
        node.firstpos = set()
        node.lastpos = set()
    elif node.type == UNION_NODE:
        if not node.left or not node.right: raise ValueError("Union node missing children")
        node.nullable = node.left.nullable or node.right.nullable
        node.firstpos = node.left.firstpos.union(node.right.firstpos)
        node.lastpos = node.left.lastpos.union(node.right.lastpos)
    elif node.type == CONCAT_NODE:
        if not node.left or not node.right: raise ValueError("Concat node missing children")
        node.nullable = node.left.nullable and node.right.nullable
        node.firstpos = node.left.firstpos.union(node.right.firstpos) if node.left.nullable else node.left.firstpos
        node.lastpos = node.right.lastpos.union(node.left.lastpos) if node.right.nullable else node.right.lastpos
    elif node.type == STAR_NODE:
        if not node.left: raise ValueError("Star node missing child")
        node.nullable = True
        node.firstpos = node.left.firstpos
        node.lastpos = node.left.lastpos
    elif node.type == PLUS_NODE:
        if not node.left: raise ValueError("Plus node missing child")
        node.nullable = node.left.nullable
        node.firstpos = node.left.firstpos
        node.lastpos = node.left.lastpos

def compute_followpos(node):
    if node is None: return

    compute_followpos(node.left)
    compute_followpos(node.right)

    if node.type == CONCAT_NODE:
        if not node.left or not node.right: raise ValueError("Concat node missing children for followpos")
        for pos_i_obj in node.left.lastpos:
            pos_i_obj.followpos.update(node.right.firstpos)        
    elif node.type == STAR_NODE:
        if not node.left: raise ValueError("Star node missing child for followpos")
        for pos_i_obj in node.left.lastpos:
            pos_i_obj.followpos.update(node.left.firstpos)
    elif node.type == PLUS_NODE:
        if not node.left: raise ValueError("Plus node missing child for followpos")
        for pos_i_obj in node.left.lastpos:
            pos_i_obj.followpos.update(node.left.firstpos)

def regex_to_direct_dfa(regex_str, pattern_name_for_dfa):
    PositionNode.reset_id_counter()
    position_nodes_map = {} 
    
    if not regex_str:
        dfa_empty_regex = DFA()
        dfa_empty_regex.start_state_id = dfa_empty_regex._get_dfa_state_id(frozenset([-2]))
        return dfa_empty_regex, None, None
    
    if regex_str == EPSILON:
        dfa_epsilon_regex = DFA()
        dfa_epsilon_regex.start_state_id = dfa_epsilon_regex._get_dfa_state_id(frozenset([-1]))
        dfa_epsilon_regex.set_accept_state(dfa_epsilon_regex.start_state_id, pattern_name_for_dfa)
        return dfa_epsilon_regex, AugmentedRegexSyntaxTreeNode(EPSILON, EPSILON_NODE), {}


    root, end_marker_char = build_augmented_syntax_tree(regex_str, position_nodes_map)
    
    if not root:
        dfa_fail = DFA()
        return dfa_fail, None, None

    compute_functions(root)
    compute_followpos(root)

    dfa = DFA()
    dfa_states_map = {} 
    unmarked_dfa_states_pos_id_sets = [] 

    s0_positions_nodes = root.firstpos
    s0_positions_ids = frozenset(p.id for p in s0_positions_nodes)

    if not s0_positions_ids and not root.nullable:
        dfa.start_state_id = dfa._get_dfa_state_id(frozenset([-2]))
        current_alphabet = set()
        for pos_node_obj in position_nodes_map.values():
            if pos_node_obj.symbol != end_marker_char and pos_node_obj.symbol != EPSILON:
                current_alphabet.add(pos_node_obj.symbol)
        dfa.alphabet = current_alphabet
        return dfa, root, position_nodes_map
    
    if not s0_positions_ids and root.nullable:
        dfa.start_state_id = dfa._get_dfa_state_id(frozenset([-1]))
        dfa.set_accept_state(dfa.start_state_id, pattern_name_for_dfa)
        current_alphabet = set()
        for pos_node_obj in position_nodes_map.values():
            if pos_node_obj.symbol != end_marker_char and pos_node_obj.symbol != EPSILON:
                current_alphabet.add(pos_node_obj.symbol)
        dfa.alphabet = current_alphabet
        return dfa, root, position_nodes_map

    dfa.start_state_id = dfa._get_dfa_state_id(s0_positions_ids)
    dfa_states_map[s0_positions_ids] = dfa.start_state_id
    unmarked_dfa_states_pos_id_sets.append(s0_positions_ids)
    
    end_marker_pos_id = None
    for pos_id_iter, pos_node_obj_iter in position_nodes_map.items():
        if pos_node_obj_iter.symbol == end_marker_char:
            end_marker_pos_id = pos_id_iter
            break
    if end_marker_pos_id is None:
        if not position_nodes_map:
             return dfa, root, position_nodes_map
        raise ValueError("End marker position not found in position_nodes_map, but positions exist.")


    current_alphabet = set()
    for pos_node_obj_iter in position_nodes_map.values():
        if pos_node_obj_iter.symbol != end_marker_char and pos_node_obj_iter.symbol != EPSILON:
            current_alphabet.add(pos_node_obj_iter.symbol)
    dfa.alphabet = current_alphabet

    processed_dfa_states_pos_id_sets = set()

    while unmarked_dfa_states_pos_id_sets:
        current_S_pos_ids = unmarked_dfa_states_pos_id_sets.pop(0)
        
        if current_S_pos_ids in processed_dfa_states_pos_id_sets : continue
        processed_dfa_states_pos_id_sets.add(current_S_pos_ids)

        current_dfa_state_id = dfa_states_map[current_S_pos_ids]

        if end_marker_pos_id in current_S_pos_ids:
            dfa.set_accept_state(current_dfa_state_id, pattern_name_for_dfa)

        for char_a in sorted(list(dfa.alphabet)):
            U_target_pos_ids = set()
            for pos_p_id in current_S_pos_ids:
                pos_p_node = position_nodes_map.get(pos_p_id)
                if pos_p_node and pos_p_node.symbol == char_a:
                    for follow_pos_node_obj in pos_p_node.followpos:
                        U_target_pos_ids.add(follow_pos_node_obj.id)
            
            U_fset_ids = frozenset(U_target_pos_ids)
            if not U_fset_ids: continue

            if U_fset_ids not in dfa_states_map:
                new_target_dfa_id = dfa._get_dfa_state_id(U_fset_ids)
                dfa_states_map[U_fset_ids] = new_target_dfa_id
                if U_fset_ids not in processed_dfa_states_pos_id_sets:
                    unmarked_dfa_states_pos_id_sets.append(U_fset_ids)
            
            target_dfa_id = dfa_states_map[U_fset_ids]
            dfa.add_transition(current_dfa_state_id, char_a, target_dfa_id)
            
    return dfa, root, position_nodes_map