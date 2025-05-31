from automata import DFA
from config import EPSILON, CONCAT_OP
from regex_utils import precedence, is_literal_char as is_simple_literal_char, preprocess_regex, infix_to_postfix
from automata import postfix_to_nfa, NFA, combine_nfas as thompson_combine_nfas, _finalize_nfa_properties


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

def _build_tree_from_single_processed_re(processed_re_str, position_nodes_map):
    operand_stack = []
    operator_stack = []

    def apply_pending_ops_for_subtree(current_op_precedence=0):
        '''
        Aplica os operadores pendendentes na pilha operator_stack as subarvores
        pendentes em operand_stack.
        Ex:
        Operand Stack pré apply:
        [Root:(union, |, N:False, F:{}, L:{})
                L---(literal, a, N:False, F:{}, L:{})
                        PosNode: Pos(1,'a')
                R---(literal, b, N:False, F:{}, L:{})
                        PosNode: Pos(2,'b')
        , Root:(literal, c, N:False, F:{}, L:{})
                PosNode: Pos(3,'c')
        ]
        Operator Stack pré apply: ['.']
        
        Operand Stack pós apply:
        [Root:(concat, ., N:False, F:{}, L:{})
                L---(union, |, N:False, F:{}, L:{})
                        L---(literal, a, N:False, F:{}, L:{})
                                PosNode: Pos(1,'a')
                        R---(literal, b, N:False, F:{}, L:{})
                                PosNode: Pos(2,'b')
                R---(literal, c, N:False, F:{}, L:{})
                        PosNode: Pos(3,'c')
        ]
        Operator Stack pós apply: []
        '''
        while operator_stack and operator_stack[-1] != '(' and \
              precedence(operator_stack[-1]) >= current_op_precedence:
            op_char = operator_stack.pop()
            
            if op_char == '*':
                if not operand_stack: raise ValueError(f"Not enough operands for * in subtree construction")
                child = operand_stack.pop()
                operand_stack.append(AugmentedRegexSyntaxTreeNode(op_char, STAR_NODE, left=child))
            elif op_char == '+': 
                if not operand_stack: raise ValueError(f"Not enough operands for + in subtree construction")
                child = operand_stack.pop()
                operand_stack.append(AugmentedRegexSyntaxTreeNode(op_char, PLUS_NODE, left=child))
            elif op_char == '?':
                if not operand_stack: raise ValueError(f"Not enough operands for ? in subtree construction")
                child_R = operand_stack.pop()
                epsilon_node_for_q = AugmentedRegexSyntaxTreeNode(EPSILON, EPSILON_NODE)
                union_node = AugmentedRegexSyntaxTreeNode('|', UNION_NODE, left=child_R, right=epsilon_node_for_q)
                operand_stack.append(union_node)
            elif op_char == CONCAT_OP or op_char == '|':
                if len(operand_stack) < 2: raise ValueError(f"Not enough operands for {op_char} in subtree construction")
                right = operand_stack.pop()
                left = operand_stack.pop()
                node_type = CONCAT_NODE if op_char == CONCAT_OP else UNION_NODE
                operand_stack.append(AugmentedRegexSyntaxTreeNode(op_char, node_type, left=left, right=right))

    # Transforma String da ER em Lista
    re_tokens = []
    temp_i = 0
    while temp_i < len(processed_re_str):
        char = processed_re_str[temp_i]
        if char == '\\':
            if temp_i + 1 < len(processed_re_str):
                re_tokens.append(processed_re_str[temp_i:temp_i+2])
                temp_i += 2
            else:
                re_tokens.append(char) 
                temp_i += 1
        else:
            re_tokens.append(char)
            temp_i += 1
    
    if not re_tokens and processed_re_str == EPSILON:
        return AugmentedRegexSyntaxTreeNode(EPSILON, EPSILON_NODE)
    if not re_tokens:
        return None

    # Adiciona literais a lista operand_stack como nodos
    # Adiciona operadores a lista operator_stack como nodos
    # Quando adicionar operadores a pilha, une as arvores adicionadas em
    # operand_stack de acordo com cada operador 
    for token_char_code in re_tokens:
        if token_char_code == EPSILON:
            operand_stack.append(AugmentedRegexSyntaxTreeNode(EPSILON, EPSILON_NODE))
        elif (len(token_char_code) == 1 and is_simple_literal_char(token_char_code)) or \
             (len(token_char_code) == 2 and token_char_code.startswith('\\')):
            actual_symbol = token_char_code[1] if len(token_char_code) == 2 and token_char_code.startswith('\\') else token_char_code
            pos_node = PositionNode(actual_symbol)
            position_nodes_map[pos_node.id] = pos_node
            node = AugmentedRegexSyntaxTreeNode(actual_symbol, LITERAL_NODE)
            node.position_node = pos_node
            operand_stack.append(node)
        elif token_char_code == '(':
            operator_stack.append(token_char_code)
        elif token_char_code == ')':
            apply_pending_ops_for_subtree(0) 
            if not operator_stack or operator_stack[-1] != '(':
                raise ValueError(f"Mismatched parentheses for subtree: {processed_re_str}")
            operator_stack.pop() 
        elif token_char_code in ['*', CONCAT_OP, '|', '?', '+']: 
            apply_pending_ops_for_subtree(precedence(token_char_code))
            operator_stack.append(token_char_code)
        else: 
            raise ValueError(f"Unknown token '{token_char_code}' in processed regex for subtree: {processed_re_str}")

    apply_pending_ops_for_subtree(0) 

    if len(operand_stack) != 1:
        if not operand_stack and not operator_stack: 
            return None 
        raise ValueError(f"Invalid expression for subtree. Final operand stack size: {len(operand_stack)} from {processed_re_str}")
    
    return operand_stack[0]

def build_augmented_syntax_tree(definitions, pattern_order, position_nodes_map, end_marker_map_ref):
    all_augmented_sub_trees = []

    # Para cada ER, montar uma arvore sintática
    for idx, pattern_name in enumerate(pattern_order):
        regex_str = definitions.get(pattern_name, "")
        if not regex_str:
            continue

        unique_end_marker_symbol_for_tree = f"_EM_{pattern_name}_{idx}" 
        
        processed_single_re_str = preprocess_regex(regex_str)
        
        if not processed_single_re_str and regex_str != EPSILON :
            continue
            
        sub_tree_root = _build_tree_from_single_processed_re(processed_single_re_str, position_nodes_map)

        if sub_tree_root is None:
            continue

        # Inclui nodo de fim de sentença na árvore
        end_pos_node = PositionNode(unique_end_marker_symbol_for_tree)
        position_nodes_map[end_pos_node.id] = end_pos_node
        end_marker_map_ref[end_pos_node.id] = pattern_name

        end_marker_tree_node = AugmentedRegexSyntaxTreeNode(unique_end_marker_symbol_for_tree, LITERAL_NODE)
        end_marker_tree_node.position_node = end_pos_node
        
        current_pattern_augmented_tree = AugmentedRegexSyntaxTreeNode(CONCAT_OP, CONCAT_NODE, 
                                                                left=sub_tree_root, 
                                                                right=end_marker_tree_node)
        all_augmented_sub_trees.append(current_pattern_augmented_tree)

    if not all_augmented_sub_trees:
        return None, ""
    
    # Une todas as ER em uma única ER utilizando |
    final_root = all_augmented_sub_trees[0]
    for tree_to_union in all_augmented_sub_trees[1:]:
        final_root = AugmentedRegexSyntaxTreeNode('|', UNION_NODE, left=final_root, right=tree_to_union)
    
    # Une todas as ER, porém para ser mostrado na interface, não é utilizado para dar
    # continuidade no algoritmo.
    re_strings_for_nfa_union = []
    for pattern_name in pattern_order:
        original_re = definitions.get(pattern_name, "")
        if original_re:
            # Adiciona parenteses as subarvores que não são são contidas por parenteses.
            if len(original_re) > 1 and not (original_re.startswith('(') and original_re.endswith(')')) and not (original_re.startswith('[') and original_re.endswith(']')):
                 re_strings_for_nfa_union.append(f"({original_re})")
            else:
                 re_strings_for_nfa_union.append(original_re)

    combined_re_str_for_nfa_display = "|".join(re_strings_for_nfa_union)
    
    return final_root, combined_re_str_for_nfa_display


def compute_functions(node):
    '''
    Calcula nullable, firstpos e lastpos de uma dada árvore.
    '''
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
    '''
    Calcula followpos de uma dada árvore.
    '''
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


def regex_to_direct_dfa(definitions, pattern_order):
    PositionNode.reset_id_counter()
    NFA.reset_state_ids() 
    position_nodes_map = {} 
    end_marker_pos_id_to_pattern_name = {}
    
    pseudo_nfa_for_display = None

    if not definitions or not pattern_order:
        dfa_empty_input = DFA()
        dfa_empty_input.start_state_id = dfa_empty_input._get_dfa_state_id(frozenset([-2])) 
        return dfa_empty_input, None, {}, None

    root, combined_re_for_nfa_display = build_augmented_syntax_tree(
        definitions, pattern_order, 
        position_nodes_map, 
        end_marker_pos_id_to_pattern_name
    )
    
    if combined_re_for_nfa_display:
        try:
            for i, po_name in enumerate(pattern_order):
                orig_re = definitions.get(po_name)
                if orig_re:
                    # We need to give unique names if we were to use thompson_combine_nfas directly
                    # Or, build one NFA from the (R1)|(R2)|... string.
                    # Let's try the latter, as it's simpler for display.
                    # The combined_re_for_nfa_display is already R1|R2|...
                    pass # No, we need individual NFAs if we want to use thompson_combine_nfas

            nfas_map_for_thompson_combine = {}
            for po_name in pattern_order:
                regex_str = definitions.get(po_name, "")
                if regex_str:
                    postfix_tokens = infix_to_postfix(regex_str)
                    nfa = postfix_to_nfa(postfix_tokens)
                    if nfa:
                        nfas_map_for_thompson_combine[po_name] = nfa
            
            if nfas_map_for_thompson_combine:
                nfa_start_state, nfa_accept_map, _ = thompson_combine_nfas(nfas_map_for_thompson_combine)
                if nfa_start_state:
                    pseudo_nfa_for_display = NFA(nfa_start_state, None) 
                    # _finalize_nfa_properties(pseudo_nfa_for_display) # This is done by get_nfa_details_str logic
                    pseudo_nfa_for_display.accept_map_for_display = nfa_accept_map 
            
        except Exception:
            pseudo_nfa_for_display = None # Failed to create for display

    if root is None: 
        dfa_no_valid_patterns = DFA()
        dfa_no_valid_patterns.start_state_id = dfa_no_valid_patterns._get_dfa_state_id(frozenset([-2]))
        return dfa_no_valid_patterns, None, position_nodes_map, pseudo_nfa_for_display

    compute_functions(root)
    compute_followpos(root)

    dfa = DFA()
    dfa_states_map = {} 
    unmarked_dfa_states_pos_id_sets = [] 

    s0_positions_nodes = root.firstpos
    s0_positions_ids = frozenset(p.id for p in s0_positions_nodes)

    # Obtem alfabeto do automato
    current_alphabet = set()
    for pos_id, pos_node_obj in position_nodes_map.items():
        if pos_id not in end_marker_pos_id_to_pattern_name: 
            if pos_node_obj.symbol != EPSILON: # Epsilon itself is not part of the alphabet
                current_alphabet.add(pos_node_obj.symbol)
    dfa.alphabet = current_alphabet

    if not s0_positions_ids and not root.nullable:
        dfa.start_state_id = dfa._get_dfa_state_id(frozenset([-2]))
        return dfa, root, position_nodes_map, pseudo_nfa_for_display
    
    # Estado inicial é o firstpos do nodo raiz
    dfa.start_state_id = dfa._get_dfa_state_id(s0_positions_ids)
    dfa_states_map[s0_positions_ids] = dfa.start_state_id
    if s0_positions_ids or root.nullable : 
      unmarked_dfa_states_pos_id_sets.append(s0_positions_ids)
    
    processed_dfa_states_pos_id_sets = set()

    # Constroi automato a partir da arvore de sintaxe
    while unmarked_dfa_states_pos_id_sets:
        current_S_pos_ids = unmarked_dfa_states_pos_id_sets.pop(0)
        
        if current_S_pos_ids in processed_dfa_states_pos_id_sets : continue
        processed_dfa_states_pos_id_sets.add(current_S_pos_ids)

        current_dfa_state_id = dfa_states_map[current_S_pos_ids]

        # Verifica se o estado atual é um estado de aceitação ao observar
        # todos os ids de estado que formam o estado atual
        accepting_patterns_for_current_dfa_state = {} 
        for pos_id_in_current_S in current_S_pos_ids:
            if pos_id_in_current_S in end_marker_pos_id_to_pattern_name:
                pattern_name = end_marker_pos_id_to_pattern_name[pos_id_in_current_S]
                try:
                    priority = pattern_order.index(pattern_name)
                    accepting_patterns_for_current_dfa_state[pattern_name] = priority
                except ValueError: 
                    pass 
        
        # Se for um estado de aceitação, entre as ERs, escolhe a de maior prioridade
        # para ser a do estado de aceitação pro caso de existirem mais de uma para
        # aquele estado
        if accepting_patterns_for_current_dfa_state:
            best_pattern_to_accept = min(accepting_patterns_for_current_dfa_state, 
                                         key=accepting_patterns_for_current_dfa_state.get)
            dfa.set_accept_state(current_dfa_state_id, best_pattern_to_accept)

        # Descobre novos estados a partir dos followpos dos estados que nomeiam
        # o estado atual
        for char_a in sorted(list(dfa.alphabet)):
            # Descobre estado a partir do atual
            U_target_pos_ids = set()
            for pos_p_id in current_S_pos_ids:
                pos_p_node = position_nodes_map.get(pos_p_id)
                if pos_p_node and pos_p_node.symbol == char_a:
                    for follow_pos_node_obj in pos_p_node.followpos:
                        U_target_pos_ids.add(follow_pos_node_obj.id)
            
            U_fset_ids = frozenset(U_target_pos_ids)
            if not U_fset_ids: continue

            # Se o estado não existe ainda, adiciona a lista de estados
            # não marcados
            if U_fset_ids not in dfa_states_map:
                new_target_dfa_id = dfa._get_dfa_state_id(U_fset_ids)
                dfa_states_map[U_fset_ids] = new_target_dfa_id
                if U_fset_ids not in processed_dfa_states_pos_id_sets:
                    unmarked_dfa_states_pos_id_sets.append(U_fset_ids)
            
            target_dfa_id = dfa_states_map[U_fset_ids]
            dfa.add_transition(current_dfa_state_id, char_a, target_dfa_id)
            
    return dfa, root, position_nodes_map, pseudo_nfa_for_display