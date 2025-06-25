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
        
        # Primeira regra:
        # If X is a terminal, then FIRST(X)= {X}.
        for t in self.grammar.terminals:
            self.first_sets[t] = {t}
        
        
        # TODO Estamos calculando first de uma maneira ineficiente, talvez algo
        # parecido com uma busca em profundidade seja melhor
        changed = True
        while changed:
            changed = False
            for p in self.grammar.productions:
                # TODO Essa checagem me parece um erro, se o simbolo
                # não está no set de firsts então quer dizer que deixamos passar
                # uma gramática mal formada, pois já preenchemos o set de firsts
                # anteriormente
                if p.head not in self.first_sets: continue
                
                original_first_set_size = len(self.first_sets[p.head])
                
                rhs_first = self._compute_first_for_sequence(p.body)
                self.first_sets[p.head].update(rhs_first)

                if len(self.first_sets[p.head]) != original_first_set_size:
                    changed = True
        return self.first_sets

    def _compute_first_for_sequence(self, sequence):
        # Essa chegagem serve para verificar se a lista é vazia, é útil para
        # poder chamar essa função ao computar follow
        if not sequence:
            return {self.grammar.epsilon_symbol}
        
        result = set()
        # Itera sobre todos os simbolos da sequencia
        for symbol in sequence:
            # TODO Essa checagem me parece um erro, se o simbolo
            # não está no set de firsts então quer dizer que deixamos passar
            # uma gramática mal formada, pois já preenchemos o set de firsts
            # anteriormente
            if symbol not in self.first_sets:
                self.first_sets[symbol] = {symbol}
            
            symbol_first = self.first_sets.get(symbol)
            result.update(symbol_first - {self.grammar.epsilon_symbol})
            # Se o simbolo atual não contém epsilon no seu first, retorna
            if self.grammar.epsilon_symbol not in symbol_first:
                return result
        # Se o for terminou, todos os simbolos tem epsilon no first,
        # logo epsilon pertence ao first
        result.add(self.grammar.epsilon_symbol)
        return result

    def compute_follow_sets(self):
        if not self.first_sets:
            self.compute_first_sets()

        self.follow_sets = {nt: set() for nt in self.grammar.non_terminals}
        start_symbol = self.grammar.augmented_start_symbol
        # Regra 1: Place $ in FOLLOW(S),where S is the start symbol, and $ is the input
        # right endmarker.
        if start_symbol:
            self.follow_sets[start_symbol] = {'$'}

        changed = True
        while changed:
            changed = False
            for p in self.grammar.productions:
                # Regra 2: Para produções A -> αBβ, Follow(B) contém First(β) - {ε}
                for i in range(len(p.body)):
                    B = p.body[i]
                    # Itera até encontrar um não terminal
                    if B in self.grammar.non_terminals:
                        # Obtem a sequencia logo após o não terminal e calcula seu first
                        beta = p.body[i+1:]
                        first_of_beta = self._compute_first_for_sequence(beta)
                        
                        # Atualiza follow de B com o first da sequencia beta
                        original_size = len(self.follow_sets[B])
                        self.follow_sets[B].update(first_of_beta - {self.grammar.epsilon_symbol})
                        if len(self.follow_sets[B]) != original_size:
                            changed = True

                # Regra 3: Para produções A -> αB ou A -> αBβ onde First(β) contém ε,
                # Follow(B) contém Follow(A)
                for i in range(len(p.body)):
                    B = p.body[i]
                    # Itera até encontrar um não terminal
                    if B in self.grammar.non_terminals:
                        # Obtem a sequencia logo após o não terminal e calcula seu first
                        beta = p.body[i+1:]
                        first_of_beta = self._compute_first_for_sequence(beta)

                        if self.grammar.epsilon_symbol in first_of_beta:
                            original_size = len(self.follow_sets[B])
                            self.follow_sets[B].update(self.follow_sets.get(p.head, set()))
                            if len(self.follow_sets[B]) != original_size:
                                changed = True
        return self.follow_sets

    def lr0_closure(self, items):
        closure = set(items)
        worklist = list(items)
        while worklist:
            item_prod, item_dot_pos = worklist.pop(0)
            if item_dot_pos < len(item_prod.body):
                symbol_after_dot = item_prod.body[item_dot_pos]
                # Se o simbolo pós ponto é um não teminal
                if symbol_after_dot in self.grammar.non_terminals:
                    # Para cada produção da gramática que comece com o
                    # não terminal precedido pelo ponto, adiciona ao closure
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
        
        # Lista para armazenar itens que o goto ainda não foi calculado
        worklist = [0]
        # Variável de controle para iterar sobre a lista de itens
        head = 0
        while head < len(worklist):
            # Obtem item atual para trabalhar sobre
            current_state_idx = worklist[head]
            # Avança na lista de itens para proxima iteração
            head += 1
            
            # Obtem todas as produções do item atual
            current_items = self.canonical_collection[current_state_idx]

            all_symbols = self.grammar.terminals.union(self.grammar.non_terminals)
            # Para cada simbolo da gramática
            for symbol in sorted(list(all_symbols)):
                # Calcula o GOTO por aquele simbolo
                next_items_set = self.lr0_goto(current_items, symbol)
                # Se GOTO não é vazio
                if next_items_set:
                    # Se GOTO não foi adiciona na coleção ainda
                    if next_items_set not in states_map:
                        # Adiciona GOTO a coleção de itens
                        states_map[next_items_set] = len(self.canonical_collection)
                        self.canonical_collection.append(next_items_set)
                        worklist.append(len(self.canonical_collection) - 1)
                    
                    # Armazema GOTO(Ii, symbol) = Ij em goto_map
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
                    # 2 - (c) If [S' -> S.] is in Ii, then set ACTION[i, $] to "accept".
                    if prod.head == self.grammar.augmented_start_symbol:
                        if '$' in self.action_table.get(i, {}):
                             raise ValueError(f"Conflict in state {i} on '$' (accept/shift or accept/reduce)")
                        self.action_table[i]['$'] = ('accept', prod.number)
                    # 2 - (b) If [A -> α.] is in Ii, then set ACTION[i, a] to "reduce A -> a" for all
                    # a in FOLLOW(A); here A may not be S'
                    else:
                        for term in self.follow_sets.get(prod.head, []):
                            if term in self.action_table.get(i, {}):
                                existing_action = self.action_table[i][term]
                                raise ValueError(f"Conflict in state {i} on '{term}': existing {existing_action[0]}, new reduce")
                            self.action_table[i][term] = ('reduce', prod.number)

            # 2 - (a) If [A -> αa.β] is in Ii and GOTO(Ii,a) = Ij, then set ACTION[i, a] to
            # "shift j." Here a must be a terminal.
            for symbol in self.grammar.terminals:
                # TODO Me parece que sempre está no map e se não está é um erro
                if (i, symbol) in self.goto_map:
                    j = self.goto_map[(i, symbol)]
                    if symbol in self.action_table.get(i, {}):
                        existing_action = self.action_table[i][symbol]
                        raise ValueError(f"Shift/Reduce conflict in state {i} on symbol '{symbol}', existing {existing_action}")
                    self.action_table[i][symbol] = ('shift', j)

            for symbol in self.grammar.non_terminals:
                # TODO Possivelmente precisa de algo assim aqui?
                # O livro não descreve, talvez não precise por que não tem como dar conflito
                # if symbol in self.goto_table.get(i, {}):
                #     raise ValueError(f"Conflict in state {i} on non terminal '{symbol}', existing {existing_action}")
                # TODO Me parece que sempre está no map e se não está é um erro
                if (i, symbol) in self.goto_map:
                    self.goto_table[i][symbol] = self.goto_map[(i, symbol)]

        return self.action_table, self.goto_table