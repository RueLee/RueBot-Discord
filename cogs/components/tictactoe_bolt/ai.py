import copy
import math
import pickle
import random

Q_TABLE_FILENAME = "cogs/components/tictactoe_bolt/rl_q_table.pkl"

def save_q_table(q_table: dict):
    with open(Q_TABLE_FILENAME, "wb") as q_file:
        pickle.dump(q_table, q_file)
        q_file.close()

def load_q_table() -> dict:
    try:
        with open(Q_TABLE_FILENAME, "rb") as q_file:
            q_table = pickle.load(q_file)
            q_file.close()
        return q_table
    except FileNotFoundError:
        return {}
    
class MCTSNode:
    def __init__(self, board, parent=None, move: (int, int)=()):
        self.board = board
        self.turns = self.board.get_current_turns()
        self.all_moves = self.board.get_all_possible_moves()
        random.shuffle(self.all_moves)
        self.move = move
        self.parent = parent
        self.children = []
        self.wins = 0
        self.total = 0

    def compute_uct(self, c=math.sqrt(2)):
        if self.total <= 0:
            return 0

        win_prob = self.wins / self.total
        uct = win_prob + c * math.sqrt(math.log(self.parent.total) / self.total)
        return uct

class Board_AI:
    def __init__(self, board, symbol: str, lr=0.2, gamma=0.9, epsilon=0.2):
        self.board = board
        self.symbol = symbol
        self.iteration = 100
        self.mcts = None

        # Q-Learning Variables
        self.alpha = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = load_q_table()

    def choose_action(self, state):
        if random.uniform(0, 1) < self.epsilon:
            # print("Using MCTS")
            self.mcts = MCTSNode(self.board)
            for i in range(self.iteration):
                self.selection()
                self.expansion()
                is_win_or_tie = self.simulate()
                self.backpropagate(is_win_or_tie)

            children_uct = [c.compute_uct() for c in self.mcts.children]
            max_uct = max(children_uct)
            uct_index = children_uct.index(max_uct)
            return self.mcts.children[uct_index].move
        else:
            # print("Using q_table")
            all_moves = self.board.get_all_possible_moves()
            q_values = [self.q_table.get((state, action), 0.0) for action in all_moves]
            max_q = max(q_values)
            if q_values.count(max_q) > 1:
                best_moves = [i for i in range(len(all_moves)) if q_values[i] == max_q]
                i = random.choice(best_moves)
            else:
                i = q_values.index(max_q)
            return all_moves[i]

    def update_q_value(self, state, action, reward, next_state, next_action):
        old_q = self.q_table.get((state, action), 0.0)
        future_q = 0
        if next_action:
            future_q = max([self.q_table.get((next_state, a), 0.0) for a in next_action])
        self.q_table[(state, action)] = old_q + self.alpha * (reward + self.gamma * future_q - old_q)

    def selection(self):
        while len(self.mcts.children) > 0:
            children_uct = [c.compute_uct() for c in self.mcts.children]
            max_uct = max(children_uct)
            uct_index = children_uct.index(max_uct)
            self.mcts = self.mcts.children[uct_index]

    def expansion(self):
        board_cpy = copy.deepcopy(self.mcts.board)
        move_pick = self.mcts.all_moves.pop()
        board_cpy.make_move(move_pick)
        board_cpy.cycle_turns()
        self.mcts.children.append(MCTSNode(board_cpy, self.mcts, move_pick))
        self.mcts = self.mcts.children[-1]

    def simulate(self):
        sim_board_cpy = copy.deepcopy(self.mcts.board)
        winner_symbol = sim_board_cpy.check_winning_position()
        while winner_symbol != "" and sim_board_cpy.turn_counter < sim_board_cpy.max_turns:
            all_moves = sim_board_cpy.get_all_possible_moves()
            random_move = random.choice(all_moves)
            sim_board_cpy.make_move(random_move)
            sim_board_cpy.cycle_turns()
        return winner_symbol == self.symbol

    def backpropagate(self, is_win: bool):
        while True:
            if is_win:
                self.mcts.wins += 1

            self.mcts.total += 1

            if self.mcts.parent is None:
                break
            self.mcts = self.mcts.parent
            is_win = not is_win
