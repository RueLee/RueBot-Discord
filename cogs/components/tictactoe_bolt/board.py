import random

class InvalidMoveError(Exception):
    pass

BOARD_EMOTE_CONVERSION = {
    "O": ":regional_indicator_o:",
    "X": ":regional_indicator_x:",
    "o": ":o:",
    "x": ":x:",
    ".": ":black_small_square:"
}

class Board:
    def __init__(self, player_o: str, player_x: str):
        self.row = 3
        self.col = 3
        self.curr_turn = random.choice(["O", "X"])
        # self.curr_turn = "O"
        self.player_sym_def = {
            "O": player_o,
            "X": player_x
        }
        self.turn_counter = 0
        self.max_turns = 20
        self.move_queue = []
        self.board = [["."] * 3 for _ in range(self.row)]

    def get_current_turns(self):
        return self.curr_turn

    def cycle_turns(self) -> None:
        self.curr_turn = "O" if self.curr_turn == "X" else "X"

    def make_move(self, move: (int, int)) -> None:
        if not self.is_in_board(move):
            raise InvalidMoveError

        if self.board[move[0]][move[1]] != ".":
            raise InvalidMoveError

        self.board[move[0]][move[1]] = self.curr_turn
        self.move_queue.append(move)
        if len(self.move_queue) >= 7:
            self.board[self.move_queue[0][0]][self.move_queue[0][1]] = "."
            self.move_queue.pop(0)

        if len(self.move_queue) >= 6:
            move_x = self.move_queue[0][0]
            move_y = self.move_queue[0][1]
            self.board[move_x][move_y] = "o" if self.board[move_x][move_y] == "O" else "x"

        self.turn_counter += 1


    def get_all_possible_moves(self) -> (int, int):
        return [(row, col) for row in range(self.row) for col in range(self.col) if self.board[row][col] == "."]

    def check_winning_position(self) -> str:
        for row in range(self.row):
            counter = 0
            curr_symbol = self.board[row][0]
            for col in range(self.col):
                if curr_symbol != self.board[row][col] or curr_symbol == ".":
                    break

                counter += 1
                if counter >= 3:
                    return curr_symbol

        for col in range(self.col):
            counter = 0
            curr_symbol = self.board[0][col]
            for row in range(self.row):
                if curr_symbol != self.board[row][col] or curr_symbol == ".":
                    break

                counter += 1
                if counter >= 3:
                    return curr_symbol

        counter = 0
        curr_symbol = self.board[0][0]
        for diagonal in range(self.row):
            if curr_symbol != self.board[diagonal][diagonal] or curr_symbol == ".":
                break

            counter += 1
            if counter >= 3:
                return curr_symbol

        counter = 0
        curr_symbol = self.board[2][0]
        for diagonal in range(1, self.row + 1):
            if curr_symbol != self.board[-diagonal][diagonal - 1] or curr_symbol == ".":
                break

            counter += 1
            if counter >= 3:
                return curr_symbol

        return ""

    def get_board_string(self) -> str:
        result_str = ""
        for row in range(self.row):
            for col in range(self.col):
                result_str += BOARD_EMOTE_CONVERSION[self.board[row][col]]
            result_str += "\n"
        return result_str

    def is_in_board(self, move: (int, int)) -> bool:
        x_pos = move[0]
        y_pos = move[1]
        return x_pos >= 0 and x_pos < self.row and y_pos >= 0 and y_pos < self.col
