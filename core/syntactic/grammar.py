import re

class Production:
    def __init__(self, head, body, number):
        self.head = head
        self.body = body
        self.number = number

    def __repr__(self):
        body_str = ' '.join(self.body) if self.body else '&'
        return f"({self.number}) {self.head} ::= {body_str}"
    
    def __eq__(self, other):
        return isinstance(other, Production) and self.number == other.number

    def __hash__(self):
        return hash(self.number)

class Grammar:
    def __init__(self):
        self.productions = []
        self.terminals = set()
        self.non_terminals = set()
        self.start_symbol = None
        self.augmented_start_symbol = None
        self.epsilon_symbol = '&'

    @staticmethod
    def from_text(grammar_text, epsilon_symbol='&'):
        grammar = Grammar()
        grammar.epsilon_symbol = epsilon_symbol
        
        processed_lines = []
        raw_lines = grammar_text.splitlines()
        for line in raw_lines:
            line_without_comment = line.split('//')[0].strip()
            if line_without_comment and not line_without_comment.startswith('#'):
                processed_lines.append(line_without_comment)

        if not processed_lines:
            raise ValueError("Grammar text is empty or only contains comments.")

        for line in processed_lines:
            if '::=' not in line:
                raise ValueError(f"Malformed production (missing '::='): {line}")
            head, _ = line.split('::=', 1)
            grammar.non_terminals.add(head.strip())
        
        if not grammar.non_terminals:
             raise ValueError("No non-terminals found in grammar.")

        first_head, _ = processed_lines[0].split('::=', 1)
        grammar.start_symbol = first_head.strip()
        grammar.augmented_start_symbol = f"{grammar.start_symbol}'"
        while grammar.augmented_start_symbol in grammar.non_terminals:
            grammar.augmented_start_symbol += "'"

        grammar.non_terminals.add(grammar.augmented_start_symbol)
        aug_prod = Production(grammar.augmented_start_symbol, [grammar.start_symbol], 0)
        grammar.productions.append(aug_prod)

        prod_num = 1
        for line in processed_lines:
            head, body_str = line.split('::=', 1)
            head = head.strip()
            
            alternative_bodies = [b.strip() for b in body_str.split('|')]
            
            for single_body_str in alternative_bodies:
                special_symbols = ['*', '+', '(', ')', ';', '=', '&']
                
                spaced_body_str = single_body_str
                for symbol in special_symbols:
                    spaced_body_str = spaced_body_str.replace(symbol, f' {symbol} ')
                
                body_symbols_raw = [s for s in spaced_body_str.strip().split(' ') if s]

                if body_symbols_raw == [grammar.epsilon_symbol] or not body_symbols_raw:
                    body_symbols = []
                else:
                    body_symbols = body_symbols_raw

                production = Production(head, body_symbols, prod_num)
                grammar.productions.append(production)
                prod_num += 1

                for symbol in body_symbols:
                    if symbol not in grammar.non_terminals:
                        grammar.terminals.add(symbol)
        
        return grammar

    def __str__(self):
        output = [f"Start Symbol: {self.start_symbol}"]
        output.append(f"Augmented Start Symbol: {self.augmented_start_symbol}")
        output.append(f"Terminals: {{ {', '.join(sorted(list(self.terminals)))} }}")
        output.append(f"Non-Terminals: {{ {', '.join(sorted(list(self.non_terminals)))} }}")
        output.append("\nProductions:")
        for p in self.productions:
            output.append(f"  {p}")
        return "\n".join(output)
