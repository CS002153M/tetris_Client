import time
from random import choice, random

from field import Field, Tetromino
import tkinter as tk
from tkinter import ttk


class TetrisApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Tetris")
        self.master.geometry("650x800")

        self.canvas = tk.Canvas(self.master, bg="black", width=600, height=900)
        self.canvas.pack()

        self.field = Field()

        self.cell_size = 40  # pixels
        self.canvas_grid = [[None for _ in range(self.field.cols)] for _ in range(self.field.rows)]
        self.next_tetromino = self.random_tetromino()
        self.next_piece_canvas = self.canvas.create_rectangle(500, 20, 580, 100, outline="white")
        self.draw_next_piece()
        self.left_moved = False

        self.current_tetromino = self.random_tetromino()
        self.current_row = 0
        self.current_col = (self.field.cols // 2) - 2
        self.current_rotation = 0
        self.drop_time = 300

        self.das_time = 133  # Delayed Auto-Shift time in milliseconds
        self.arr_time = 10  # Auto-Repeat Rate time in milliseconds
        self.last_keypress_time = 0  # Time of last directional key press
        self.key_held_down = None  # None, 'Left', or 'Right'

        for i in range(self.field.rows):
            for j in range(self.field.cols):
                x1 = j * self.cell_size
                y1 = i * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                self.canvas_grid[i][j] = self.canvas.create_rectangle(x1, y1, x2, y2, fill="black", outline="black",
                                                                      width=0)

        self.draw_lines()

        self.update_grid()
        self.master.after(self.drop_time, self.game_loop)

        self.master.bind('w', self.rotate)
        self.master.bind('<Up>', self.rotate)
        self.master.bind('a', self.move_left)
        self.master.bind('<Left>', self.move_left)
        self.master.bind('s', self.move_down)
        self.master.bind('<Down>', self.move_down)
        self.master.bind('d', self.move_right)
        self.master.bind('<Right>', self.move_right)

        self.master.bind('<KeyRelease-a>', self.reset_key_held_down)
        self.master.bind('<KeyRelease-Left>', self.reset_key_held_down)
        self.master.bind('<KeyRelease-d>', self.reset_key_held_down)
        self.master.bind('<KeyRelease-Right>', self.reset_key_held_down)

        self.master.bind('<space>', self.hard_drop)
        self.master.focus_set()
        # ttk.Button(self.master, text="Update", command=self.update_tetromino).grid(row=self.field.rows,
                                                                                   #columnspan=self.field.cols)

    def draw_next_piece(self):
        # First, clear the old next piece from the canvas
        self.canvas.delete("next_piece")

        shape = Tetromino(self.next_tetromino).value["shape"][0]
        offset = Tetromino(self.next_tetromino).value["offset"]
        for dx, row in enumerate(shape):
            for dy, cell in enumerate(row):
                if cell:
                    x1 = offset[0] + 510 + dy * self.cell_size / 2
                    y1 = offset[1] + 40 + dx * self.cell_size / 2
                    x2 = x1 + self.cell_size / 2
                    y2 = y1 + self.cell_size / 2
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.next_tetromino.value["color"],
                                                 tags="next_piece")

    def draw_lines(self):
        # Now draw plusses at intersections
        for i in range(self.field.rows + 1):
            for j in range(self.field.cols + 1):
                x = j * self.cell_size
                y = i * self.cell_size
                plus_size = 7  # The size of each arm of the plus

                # Draw the vertical and horizontal lines (bars) connecting the plusses
                if i < self.field.rows:
                    self.canvas.create_line(x, y, x, y + self.cell_size, fill="#1f1f1f", width=0.2)
                if j < self.field.cols:
                    self.canvas.create_line(x, y, x + self.cell_size, y, fill="#1f1f1f", width=0.2)

                # Draw the plus at each intersection point
                self.canvas.create_line(x - plus_size, y, x + plus_size, y, fill="#2d2e2d", width=0.7)
                self.canvas.create_line(x, y - plus_size, x, y + plus_size, fill="#2d2e2d", width=0.7)

    def random_tetromino(self):
        return choice(list(Tetromino))

    def update_grid(self):
        for i in range(self.field.rows):
            for j in range(self.field.cols):
                color = "black"
                if self.field.board[i][j] != 0:
                    tetromino_type = self.field.board[i][j]
                    color = Tetromino(tetromino_type).value["color"]

                self.canvas.itemconfig(self.canvas_grid[i][j], fill=color)

        shape = Tetromino(self.current_tetromino).value["shape"][self.current_rotation]

        # Calculate the ghost (or shadow) tetromino
        ghost_row = self.current_row
        while not self.field.check_collision(self.current_tetromino, self.current_rotation, ghost_row + 1,
                                             self.current_col):
            ghost_row += 1

        # Overlay the ghost tetromino
        for dx, row in enumerate(shape):
            for dy, cell in enumerate(row):
                if cell:
                    self.canvas.itemconfig(self.canvas_grid[ghost_row + dx][self.current_col + dy], fill="gray")

        # Overlay the current tetromino
        for dx, row in enumerate(shape):
            for dy, cell in enumerate(row):
                if cell:
                    self.canvas.itemconfig(self.canvas_grid[self.current_row + dx][self.current_col + dy], fill=self.current_tetromino.value["color"])


    def game_loop(self):
        if self.current_row == 0:
            self.current_tetromino = self.next_tetromino
            self.next_tetromino = self.random_tetromino()
            self.draw_next_piece()

            self.left_moved = False

        if not self.field.check_collision(self.current_tetromino, self.current_rotation, self.current_row + 1, self.current_col):
            self.current_row += 1
        else:
            if self.current_row == 0:
                self.field = Field()
            self.field.place_tetromino(self.current_tetromino, self.current_rotation, self.current_col)
            self.current_tetromino = self.next_tetromino
            self.current_row = 0
            self.current_col = (self.field.cols // 2) - 2
            self.current_rotation = 0
            self.key_held_down = None

        if self.key_held_down:
            current_time = time.time() * 1000  # Current time in milliseconds
            elapsed_time = current_time - self.last_keypress_time

            if elapsed_time > self.das_time:
                if (current_time - self.last_keypress_time) % self.arr_time < self.arr_time / 2:
                    if self.key_held_down == 'Left':
                        self.move_left()
                    elif self.key_held_down == 'Right':
                        self.move_right()

        self.update_grid()
        self.master.after(self.drop_time, self.game_loop)

    def rotate(self, event=None):
        new_rotation = (self.current_rotation + 1) % len(Tetromino(self.current_tetromino).value["shape"])
        if not self.field.check_collision(self.current_tetromino, new_rotation, self.current_row, self.current_col):
            if len(self.current_tetromino.value["shape"]) < new_rotation:
                new_rotation -= len(self.current_tetromino.value["shape"])
            self.current_rotation = new_rotation
            if Tetromino(self.current_tetromino).value["left_move"].__contains__(new_rotation) and not self.left_moved:
                self.current_col -= 1
                self.left_moved = True
            elif self.left_moved:
                self.current_col += 1
                self.left_moved = False

            if new_rotation % 2 == 0:
                self.current_col -= 1
            else:
                self.current_col += 1
            self.update_grid()

    def reset_key_held_down(self, event=None):
        self.key_held_down = None

    def move_left(self, event=None):
        if event:  # Only set these variables if the event exists (i.e., the function was triggered by a key press)
            self.last_keypress_time = time.time() * 1000
            self.key_held_down = 'Left'
        if not self.field.check_collision(self.current_tetromino, self.current_rotation, self.current_row,
                                          self.current_col - 1):
            self.current_col -= 1
            self.update_grid()

    def move_right(self, event=None):
        if event:  # Only set these variables if the event exists (i.e., the function was triggered by a key press)
            self.last_keypress_time = time.time() * 1000
            self.key_held_down = 'Right'
        if not self.field.check_collision(self.current_tetromino, self.current_rotation, self.current_row,
                                          self.current_col + 1):
            self.current_col += 1
            self.update_grid()

    def move_down(self, event=None):
        if not self.field.check_collision(self.current_tetromino, self.current_rotation, self.current_row + 1,
                                          self.current_col):
            self.current_row += 1
            self.update_grid()

    def hard_drop(self, event=None):
        while not self.field.check_collision(self.current_tetromino, self.current_rotation, self.current_row + 1,
                                             self.current_col):
            self.current_row += 1
        self.field.place_tetromino(self.current_tetromino, self.current_rotation, self.current_col)
        self.current_tetromino = self.next_tetromino
        self.current_row = 0
        self.current_col = (self.field.cols // 2) - 2
        self.current_rotation = 0
        self.update_grid()
        self.key_held_down = None

if __name__ == '__main__':
    root = tk.Tk()
    app = TetrisApp(root)
    root.mainloop()