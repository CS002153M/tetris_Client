from enum import Enum


class Tetromino(Enum):
    I = {"shape": [[[1, 1, 1, 1]], [[1], [1], [1], [1]]], "color": "cyan", "offset": [-10, 10], "left_move": []}
    O = {"shape": [[[1, 1], [1, 1]]], "color": "yellow", "offset": [10, 0], "left_move": []}
    T = {"shape": [
        [[0, 1, 0], [1, 1, 1]],
        [[1, 0], [1, 1], [1, 0]],
        [[1, 1, 1], [0, 1, 0]],
        [[0, 1], [1, 1], [0, 1]]
    ], "color": "purple", "offset": [0, 0], "left_move": [3]}
    S = {"shape": [
        [[0, 1, 1], [1, 1, 0]],
        [[1, 0], [1, 1], [0, 1]]
    ], "color": "green", "offset": [0, 0], "left_move": []}
    Z = {"shape": [
        [[1, 1, 0], [0, 1, 1]],
        [[0, 1], [1, 1], [1, 0]]
    ], "color": "red", "offset": [0, 0], "left_move": []}
    J = {"shape": [
        [[1, 0, 0], [1, 1, 1]],
        [[1, 1], [1, 0], [1, 0]],
        [[1, 1, 1], [0, 0, 1]],
        [[0, 1], [0, 1], [1, 1]]
    ], "color": "blue", "offset": [0, 0], "left_move": [3]}
    L = {"shape": [
        [[0, 0, 1], [1, 1, 1]],
        [[1, 0], [1, 0], [1, 1]],
        [[1, 1, 1], [1, 0, 0]],
        [[1, 1], [0, 1], [0, 1]]
    ], "color": "orange", "offset": [0, 0], "left_move": [3]}


class Field:
    def __init__(self):
        self.rows = 20
        self.cols = 10
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.is_active = True

    def update_is_active(self):
        for c in range(self.cols):
            if self.board[0][c] != 0:
                self.is_active = False
                return
        self.is_active = True

    def clear_lines(self):
        rows_to_clear = []
        for i, row in enumerate(self.board):
            if all(cell != 0 for cell in row):
                rows_to_clear.append(i)

        # Remove the filled lines and add new empty lines at the top
        for i in reversed(rows_to_clear):  # Reverse so we delete from the bottom up
            del self.board[i]
            self.board.insert(0, [0 for _ in range(self.cols)])

        return len(rows_to_clear)  # Return the number of cleared lines, in case you want to use it

    def place_tetromino(self, tetromino, rotation_index, place_col):
        shape = tetromino.value["shape"][rotation_index]
        start_row = self.rows - len(shape)
        for start_row in range(self.rows - len(shape), -1, -1):
            collision = False
            for r in range(len(shape)):
                for c in range(len(shape[r])):
                    if shape[r][c] and self.board[start_row + r][place_col + c]:
                        collision = True
                        break
                if collision:
                    break
            if not collision:
                break
        if start_row >= 0:
            for r in range(len(shape)):
                for c in range(len(shape[r])):
                    if shape[r][c]:
                        self.board[start_row + r][place_col + c] = tetromino
        self.update_is_active()
        self.clear_lines()
        return start_row

    def check_collision(self, tetromino, rotation_index, row, col):
        shape = tetromino.value["shape"][rotation_index]
        for r in range(len(shape)):
            for c in range(len(shape[r])):
                if shape[r][c]:  # If this part of the tetromino is solid
                    # Check if it's out of bounds or collides with a filled square on the board
                    if row + r >= self.rows or \
                            col + c < 0 or col + c >= self.cols or \
                            self.board[row + r][col + c] != 0:
                        return True
        return False

    def __str__(self):
        return "\n".join("".join('#' if cell else '.' for cell in row) for row in self.board) + "\n"