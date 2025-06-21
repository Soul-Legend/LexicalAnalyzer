class SLRParser:
    def __init__(self, grammar, action_table, goto_table):
        self.grammar = grammar
        self.action_table = action_table
        self.goto_table = goto_table

    def parse(self, token_stream):
        token_stream.append( ('$', '$', '$') )
        
        stack = [0]
        input_ptr = 0
        parse_steps = []

        while True:
            state = stack[-1]
            token_type = token_stream[input_ptr][1]
            
            current_stack_str = ' '.join(map(str, stack))
            remaining_input_str = ' '.join([t[1] for t in token_stream[input_ptr:]])
            
            if state not in self.action_table or token_type not in self.action_table[state]:
                step_info = {
                    "stack": current_stack_str,
                    "input": remaining_input_str,
                    "action": f"ERRO: Ação não definida para estado {state} e entrada '{token_type}'"
                }
                parse_steps.append(step_info)
                return parse_steps, False, "Erro de sintaxe: Ação indefinida."

            action, value = self.action_table[state][token_type]
            
            step_info = {
                "stack": current_stack_str,
                "input": remaining_input_str,
                "action": f"{action} {value}"
            }
            
            if action == 'shift':
                stack.append(token_stream[input_ptr][1])
                stack.append(value)
                input_ptr += 1
                step_info["action"] = f"Shift para estado {value}"
            elif action == 'reduce':
                prod_num = value
                production = self.grammar.productions[prod_num]
                
                if production.body != [self.grammar.epsilon_symbol]:
                    for _ in range(2 * len(production.body)):
                        stack.pop()
                
                prev_state = stack[-1]
                stack.append(production.head)
                
                if prev_state not in self.goto_table or production.head not in self.goto_table[prev_state]:
                     step_info["action"] = f"ERRO: GOTO não definido para estado {prev_state} e não-terminal '{production.head}'"
                     parse_steps.append(step_info)
                     return parse_steps, False, "Erro de sintaxe: GOTO indefinido."
                
                next_state = self.goto_table[prev_state][production.head]
                stack.append(next_state)
                step_info["action"] = f"Reduce usando {production} e GOTO[{prev_state}, {production.head}] -> {next_state}"
            elif action == 'accept':
                step_info["action"] = "Aceitar"
                parse_steps.append(step_info)
                return parse_steps, True, "Sentença aceita com sucesso."
            else:
                step_info["action"] = f"ERRO: Ação desconhecida '{action}'"
                parse_steps.append(step_info)
                return parse_steps, False, "Erro interno do parser."

            parse_steps.append(step_info)