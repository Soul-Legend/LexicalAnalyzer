from collections import defaultdict

class SLRGenerator:
    def __init__(self, grammar):
        self.grammar = grammar
        self.first_sets = {}
        self.follow_sets = {}
        self.canonical_collection = []
        self.goto_map = {}
        self.action_table = {}
        self.goto_table = {}

    def compute_first_sets(self):
        self.first_sets = {nt: set() for nt in self.grammar.non_terminals}
        for t in self.grammar.terminals:
            self.first_sets[t] = {t}
        
        changed = True
        while changed:
            changed = False
            for p in self.grammar.productions:
                if p.head not in self.first_sets: continue
                original_first_set_size = len(self.first_sets[p.head])
                
                rhs_first = self._compute_first_for_sequence(p.body)
                self.first_sets[p.head].update(rhs_first)

                if len(self.first_sets[p.head]) != original_first_set_size:
                    changed = True
        return self.first_sets

    def _compute_first_for_sequence(self, sequence):
        if not sequence:
            return {self.grammar.epsilon_symbol}
        
        result = set()
        for symbol in sequence:
            if symbol not in self.first_sets:
                self.first_sets[symbol] = {symbol}
            
            symbol_first = self.first_sets.get(symbol)
            result.update(symbol_first - {self.grammar.epsilon_symbol})
            if self.grammar.epsilon_symbol not in symbol_first:
                return result
        result.add(self.grammar.epsilon_symbol)
        return result

    def compute_follow_sets(self):
        if not self.first_sets:
            self.compute_first_sets()

        self.follow_sets = {nt: set() for nt in self.grammar.non_terminals}
        start_symbol = self.grammar.augmented_start_symbol
        if start_symbol:
            self.follow_sets[start_symbol] = {'$'}

        changed = True
        while changed:
            changed = False
            for p in self.grammar.productions:
                trailer = set(self.follow_sets.get(p.head, set()))
                
                for i in range(len(p.body) - 1, -1, -1):
                    symbol = p.body[i]
                    if symbol in self.grammar.non_terminals:
                        original_follow_set_size = len(self.follow_sets[symbol])
                        self.follow_sets[symbol].update(trailer)
                        if len(self.follow_sets[symbol]) != original_follow_set_size:
                            changed = True
                    
                    beta_first = self._compute_first_for_sequence(p.body[i:i+1])
                    if self.grammar.epsilon_symbol in beta_first:
                        trailer.update(beta_first - {self.grammar.epsilon_symbol})
                    else:
                        trailer = beta_first
        return self.follow_sets

    def lr0_closure(self, items):
        closure = set(items)
        worklist = list(items)
        while worklist:
            item_prod, item_dot_pos = worklist.pop(0)
            if item_dot_pos < len(item_prod.body):
                symbol_after_dot = item_prod.body[item_dot_pos]
                if symbol_after_dot in self.grammar.non_terminals:
                    for p in self.grammar.productions:
                        if p.head == symbol_after_dot:
                            new_item = (p, 0)
                            if new_item not in closure:
                                closure.add(new_item)
                                worklist.append(new_item)
        return frozenset(closure)

    def lr0_goto(self, items, symbol):
        next_items_kernel = set()
        for prod, dot_pos in items:
            if dot_pos < len(prod.body) and prod.body[dot_pos] == symbol:
                next_items_kernel.add((prod, dot_pos + 1))
        return self.lr0_closure(next_items_kernel)

    def build_canonical_collection(self):
        if not self.grammar.productions: return [], {}
        
        initial_prod = self.grammar.productions[0]
        c0 = self.lr0_closure({(initial_prod, 0)})
        
        self.canonical_collection = [c0]
        states_map = {c0: 0}
        self.goto_map = {}
        
        worklist = [0]
        head = 0
        while head < len(worklist):
            current_state_idx = worklist[head]
            head += 1
            current_items = self.canonical_collection[current_state_idx]

            all_symbols = self.grammar.terminals.union(self.grammar.non_terminals)
            for symbol in sorted(list(all_symbols)):
                next_items_set = self.lr0_goto(current_items, symbol)
                if next_items_set:
                    if next_items_set not in states_map:
                        states_map[next_items_set] = len(self.canonical_collection)
                        self.canonical_collection.append(next_items_set)
                        worklist.append(len(self.canonical_collection) - 1)
                    
                    next_state_idx = states_map[next_items_set]
                    self.goto_map[(current_state_idx, symbol)] = next_state_idx
        
        return self.canonical_collection, self.goto_map

    def build_slr_table(self):
        if not self.canonical_collection:
            self.build_canonical_collection()
        if not self.follow_sets:
            self.compute_follow_sets()

        self.action_table = defaultdict(dict)
        self.goto_table = defaultdict(dict)
        
        for i, item_set in enumerate(self.canonical_collection):
            for prod, dot_pos in item_set:
                if dot_pos == len(prod.body):
                    if prod.head == self.grammar.augmented_start_symbol:
                        if '$' in self.action_table.get(i, {}):
                             raise ValueError(f"Conflict in state {i} on '$' (accept/shift or accept/reduce)")
                        self.action_table[i]['$'] = ('accept', prod.number)
                    else:
                        for term in self.follow_sets.get(prod.head, []):
                            if term in self.action_table.get(i, {}):
                                existing_action = self.action_table[i][term]
                                raise ValueError(f"Conflict in state {i} on '{term}': existing {existing_action[0]}, new reduce")
                            self.action_table[i][term] = ('reduce', prod.number)

            for symbol in self.grammar.terminals:
                 if (i, symbol) in self.goto_map:
                    j = self.goto_map[(i, symbol)]
                    if symbol in self.action_table.get(i, {}):
                        existing_action = self.action_table[i][symbol]
                        raise ValueError(f"Shift/Reduce conflict in state {i} on symbol '{symbol}', existing {existing_action}")
                    self.action_table[i][symbol] = ('shift', j)

            for symbol in self.grammar.non_terminals:
                 if (i, symbol) in self.goto_map:
                    self.goto_table[i][symbol] = self.goto_map[(i, symbol)]

        return self.action_table, self.goto_table