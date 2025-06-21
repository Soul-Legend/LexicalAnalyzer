# front/syntactic/grammar.py
import re

class Production:
    def __init__(self, head, body, number):
        self.head = head
        self.body = body
        self.number = number

    def __repr__(self):
        return f"({self.number}) {self.head} ::= {' '.join(self.body)}"
    
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
        
        lines = [line.strip() for line in grammar_text.splitlines() if line.strip() and not line.strip().startswith('#')]
        if not lines:
            raise ValueError("Grammar text is empty or only contains comments.")

        # Primeiro passo: identificar todos os não-terminais (LHS)
        for line in lines:
            if '::=' not in line:
                raise ValueError(f"Malformed production (missing '::='): {line}")
            head, _ = line.split('::=', 1)
            grammar.non_terminals.add(head.strip())
        
        if not grammar.non_terminals:
             raise ValueError("No non-terminals found in grammar.")

        # Assumir que o primeiro não-terminal definido é o símbolo inicial
        first_head, _ = lines[0].split('::=', 1)
        grammar.start_symbol = first_head.strip()
        grammar.augmented_start_symbol = f"{grammar.start_symbol}'"
        while grammar.augmented_start_symbol in grammar.non_terminals:
            grammar.augmented_start_symbol += "'"

        # Adiciona a produção aumentada
        grammar.non_terminals.add(grammar.augmented_start_symbol)
        aug_prod = Production(grammar.augmented_start_symbol, [grammar.start_symbol], 0)
        grammar.productions.append(aug_prod)

        # Segundo passo: processar produções e identificar terminais
        prod_num = 1
        for line in lines:
            head, body_str = line.split('::=', 1)
            head = head.strip()
            
            body_symbols = [s for s in body_str.strip().split(' ') if s]
            
            production = Production(head, body_symbols, prod_num)
            grammar.productions.append(production)
            prod_num += 1

            for symbol in body_symbols:
                if symbol not in grammar.non_terminals and symbol != grammar.epsilon_symbol:
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