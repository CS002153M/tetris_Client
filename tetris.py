import json
import os
import time
import tkinter as tk
from random import random
import random
from tkinter import simpledialog

import pygame
import requests
from PIL import ImageTk, ImageEnhance, Image

from field import Field, Tetromino

api = "http://localhost:6969"

class TetrisApp:
    def __init__(self, master, overlay, token):
        self.token = token
        self.active = True
        self.master = master
        self.bestMove = None

        for widget in master.winfo_children():
            widget.destroy()
        overlay.destroy()

        # Load and play background music
        pygame.mixer.music.load("assets/tetris_jazz.wav")  # Change to your actual file path
        pygame.mixer.music.play(loops=-1)  # This will start the music and loop indefinitely

        self.bag = list(Tetromino)  # Create a bag containing all seven tetrominoes
        random.shuffle(self.bag)  # Shuffle the bag
        self.shuffled_bag = []  # Create an empty list to hold the shuffled tetrominoes

        # Load images from the assets folder
        self.bg_image = tk.PhotoImage(file="assets/game_client.png")
        self.tetris_field = tk.PhotoImage(file="assets/tetris_field.png")

        self.difficulty = 1
        self.score = 0
        self.last_fall_time = time.time()
        self.last_shift_time = time.time()
        self.move_repeat_timer = 0

        # Background canvas
        self.canvas = tk.Canvas(master, width=1600, height=900, bd=0, highlightthickness=0, relief='flat')
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        self.canvas.create_image(800, 450, image=self.tetris_field, anchor="center")

        self.tetrisCanvas = tk.Canvas(self.master, bg="white", width=385.5, height=653, bd=0, highlightthickness=0, relief='flat')
        self.tetrisCanvas.place(x=607, y=137)

        self.field = Field()

        self.high_score = 0
        self.clear_api_field()
        self.load_options_from_file()

        # Load hover sound
        self.hover_sound = pygame.mixer.Sound("assets/button_hover.mp3")

        # Buttons
        self.exit_button_image = tk.PhotoImage(file="assets/client_button_exit.png")
        button_y_start_position = 60  # Starting Y position of the first button
        self.create_button(master, "Exit", "assets/client_button_exit.png", button_y_start_position)
        self.create_button(master, "Options", "assets/client_button_settings.png", button_y_start_position + self.exit_button_image.height() / 1.2)

        # Make the window moveable
        self.canvas.bind("<Button-1>", self.click_window)
        self.canvas.bind("<B1-Motion>", self.drag_window)

        # Initial position
        self._drag_data = {"x": 0, "y": 0}

        self.cell_size = 38.5  # pixels
        self.canvas_grid = [[None for _ in range(self.field.cols)] for _ in range(self.field.rows)]
        self.next_tetrominoes = [self.random_tetromino() for _ in range(4)]
        self.left_moved = False

        self.current_tetromino = self.random_tetromino()
        self.current_row = 0
        self.current_col = (self.field.cols // 2) - 2
        self.current_rotation = 0

        self.last_keypress_time = 0  # Time of last directional key press
        self.key_held_down = None  # None, 'Left', or 'Right'

        for i in range(self.field.rows):
            for j in range(self.field.cols):
                x1 = j * self.cell_size
                y1 = i * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                self.canvas_grid[i][j] = self.tetrisCanvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="white",
                                                                            width=0)

        self.draw_lines()

        self.master.bind('w', self.rotate)
        self.master.bind('<Up>', self.rotate)
        self.master.bind('a', self.move_left)
        self.master.bind('<Left>', self.move_left)
        self.master.bind('s', self.move_down)
        self.master.bind('<Down>', self.move_down)
        self.master.bind('d', self.move_right)
        self.master.bind('<Right>', self.move_right)

        self.master.bind('p', self.toggle_playing)

        self.master.bind('<KeyRelease-a>', self.reset_key_held_down)
        self.master.bind('<KeyRelease-Left>', self.reset_key_held_down)
        self.master.bind('<KeyRelease-d>', self.reset_key_held_down)
        self.master.bind('<KeyRelease-Right>', self.reset_key_held_down)

        self.master.bind('<space>', self.hard_drop)
        self.master.focus_set()

        self.activate()

    def toggle_playing(self, master):
        if self.active:
            self.deactivate()
        else:
            self.activate()

    def create_button(self, master, text, image_path, y_position):
        # Use the ImageTk.PhotoImage to load the image directly
        tk_image = ImageTk.PhotoImage(file=image_path)

        # Create a canvas window to hold the button
        button_canvas = self.canvas.create_image(1520, y_position, image=tk_image)

        # Bind mouse events to the canvas window
        self.canvas.tag_bind(button_canvas, "<Enter>", lambda e: self.on_hover(button_canvas, image_path, True, tk_image))
        self.canvas.tag_bind(button_canvas, "<Leave>", lambda e: self.on_hover(button_canvas, image_path, False, tk_image))
        self.canvas.tag_bind(button_canvas, "<Button-1>", lambda e: self.clicked(text))

        # Store a reference to the image to prevent garbage collection
        self.store_image(tk_image)

    def clicked(self, button):
        match (button):
            case "Exit":
                quit()
            case "Options":
                self.show_options_dialog()
                pass

    def show_options_dialog(self):
        # Audio setting
        self.audio_enabled = simpledialog.askstring("Audio", "Enable audio? (yes/no)",
                                                    parent=self.master)
        if self.audio_enabled is not None:
            self.audio_enabled = self.audio_enabled.lower() in ('yes', 'true', '1')

        # DAS setting
        self.das_time = simpledialog.askinteger("DAS", "Set Delayed Auto-Shift time (ms)",
                                                parent=self.master,
                                                minvalue=0, maxvalue=1000)
        try:
            self.das_time = int(self.das_time)
        except:
            self.das_time = 10

        # ARR setting
        self.arr_time = simpledialog.askinteger("ARR", "Set Auto-Repeat Rate time (ms)",
                                                parent=self.master,
                                                minvalue=0, maxvalue=1000)

        try:
            self.arr_time = int(self.arr_time)
        except:
            self.arr_time = 100

        # Difficulty setting
        self.difficulty = simpledialog.askinteger("Difficulty", "Set difficulty from 1 to 10",
                                                parent=self.master,
                                                minvalue=1, maxvalue=10)

        try:
            self.drop_time = 600 - (self.difficulty * 40)
        except:
            self.difficulty = 1
            self.drop_time = 600 - (self.difficulty * 40)

        self.save_options_to_file()

        # Update the settings in the game if needed
        # For example, if audio setting changed:
        if not self.audio_enabled:
            pygame.mixer.music.stop()
        else:
            pygame.mixer.music.play(loops=-1)

    def on_hover(self, button_canvas, image_path, hover, tk_image):
        # The hover effect now needs to apply a tint to the tk_image directly
        if hover:
            self.hover_sound.play()
            # Apply a green tint effect to the tk_image
            self.apply_green_tint(image_path, button_canvas, True, tk_image)
        else:
            # Revert the button image to the original
            self.apply_green_tint(image_path, button_canvas, False, tk_image)

    def apply_green_tint(self, image_path, button_canvas, apply_tint, tk_image):
        if apply_tint:
            # Open the original image using PIL
            original_image = Image.open(image_path)

            # Enhance the color to add a green tint
            enhancer = ImageEnhance.Color(original_image)
            tinted_image = enhancer.enhance(10)  # Adjust the factor for the desired tint intensity

            # Convert the Pillow image to a Tkinter-compatible image
            tk_tinted_image = ImageTk.PhotoImage(tinted_image)

            # Update the button's image to the tinted version
            self.canvas.itemconfig(button_canvas, image=tk_tinted_image)

            # Keep a reference to the tinted image to prevent garbage collection
            self.store_image(tk_tinted_image)
        else:
            # Revert to the original image if not hovering
            # You need to keep a reference to the original tk_image as well
            self.canvas.itemconfig(button_canvas, image=tk_image)

    def draw_next_piece(self):
        # Clear the old next pieces from the canvas
        self.tetrisCanvas.delete("next_piece")

        for index, tetromino in enumerate(self.next_tetrominoes):
            shape = Tetromino(tetromino).value["shape"][0]
            offset = Tetromino(tetromino).value["offset"]
            for dx, row in enumerate(shape):
                for dy, cell in enumerate(row):
                    if cell:
                        x1 = offset[0] + 510 + dy * self.cell_size / 2
                        y1 = offset[1] + (40 + (index * 3 * self.cell_size / 2)) + dx * self.cell_size / 2
                        x2 = x1 + self.cell_size / 2
                        y2 = y1 + self.cell_size / 2
                        self.tetrisCanvas.create_rectangle(x1, y1, x2, y2, fill=tetromino.value["color"],
                                                           tags="next_piece")

    def store_image(self, tk_image):
        # Store the Tkinter image reference to prevent garbage collection
        if not hasattr(self, 'images'):
            self.images = []
        self.images.append(tk_image)

    def draw_lines(self):
        # Now draw plusses at intersections
        for i in range(self.field.rows + 1):
            for j in range(self.field.cols + 1):
                x = j * self.cell_size
                y = i * self.cell_size
                plus_size = 7  # The size of each arm of the plus

                # Draw the vertical and horizontal lines (bars) connecting the plusses
                if i < self.field.rows:
                    self.tetrisCanvas.create_line(x, y, x, y + self.cell_size, fill="#1f1f1f", width=0.2)
                if j < self.field.cols:
                    self.tetrisCanvas.create_line(x, y, x + self.cell_size, y, fill="#1f1f1f", width=0.2)

                # Draw the plus at each intersection point
                self.tetrisCanvas.create_line(x - plus_size, y, x + plus_size, y, fill="#2d2e2d", width=0.7)
                self.tetrisCanvas.create_line(x, y - plus_size, x, y + plus_size, fill="#2d2e2d", width=0.7)

    def random_tetromino(self):
        # If the bag is running low, refill it and shuffle
        while len(self.shuffled_bag) < 4:
            self.shuffled_bag.extend(self.bag)
            random.shuffle(self.shuffled_bag)

        # Draw the next tetromino from the shuffled bag
        return self.shuffled_bag.pop()

    def update_grid(self):
        for i in range(self.field.rows):
            for j in range(self.field.cols):
                color = "white"
                if self.field.board[i][j] != 0:
                    tetromino_type = self.field.board[i][j]
                    color = Tetromino(tetromino_type).value["color"]

                self.tetrisCanvas.itemconfig(self.canvas_grid[i][j], fill=color)

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
                    self.tetrisCanvas.itemconfig(self.canvas_grid[ghost_row + dx][self.current_col + dy], fill="gray")

        if self.bestMove:
            best_row = self.current_row
            while not self.field.check_collision(self.current_tetromino, self.bestMove[0], best_row + 1,
                                                 self.bestMove[1]):
                best_row += 1

            shape = Tetromino(self.current_tetromino).value["shape"][self.bestMove[0]]
            for dx, row in enumerate(shape):
                for dy, cell in enumerate(row):
                    if cell:
                        self.tetrisCanvas.itemconfig(self.canvas_grid[best_row + dx][self.bestMove[1] + dy],
                                                     fill="black")

        # Overlay the current tetromino
        for dx, row in enumerate(shape):
            for dy, cell in enumerate(row):
                if cell:
                    self.tetrisCanvas.itemconfig(self.canvas_grid[self.current_row + dx][self.current_col + dy], fill=self.current_tetromino.value["color"])

    def deactivate(self):
        self.active = False
        self.update_grid()

    def activate(self):
        self.active = True
        self.update_grid()
        self.draw_next_piece()

        self.master.after(self.drop_time, self.game_loop)

    def load_options_from_file(self, filename="options.json"):
        # Check if the file exists before trying to open it
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                options = json.load(file)
                self.audio_enabled = options.get("audio_enabled", True)
                self.das_time = options.get("das_time", 100)
                self.arr_time = options.get("arr_time", 10)
                self.difficulty = options.get("difficulty", 1)
                self.drop_time = options.get("drop_time", 600 - (self.difficulty * 40))
                self.high_score = options.get("high_score", 0)  # Load the high score

                if not self.audio_enabled:
                    pygame.mixer.music.stop()
        else:
            # Set defaults if the options file does not exist
            self.audio_enabled = True
            self.das_time = 100
            self.arr_time = 10
            self.difficulty = 1
            self.drop_time = 600 - (self.difficulty * 40)
            self.high_score = 0

    def update_high_score(self, score):
        if score > self.high_score:
            self.high_score = score
            self.save_options_to_file()

    def game_loop(self):
        if not self.active:
            return

        current_time = time.time()
        fall_due = current_time - self.last_fall_time > self.drop_time / 1000.0
        shift_due = current_time - self.last_shift_time > self.das_time / 1000.0

        if fall_due:
            if not self.field.check_collision(self.current_tetromino, self.current_rotation, self.current_row + 1, self.current_col):
                self.current_row += 1
            else:
                self.field.place_tetromino(self.current_tetromino, self.current_rotation, self.current_col)
                cachedTetromino = self.current_tetromino

                self.current_tetromino = self.next_tetrominoes.pop(0)
                self.next_tetrominoes.append(self.random_tetromino())
                self.draw_next_piece()
                self.score += 10

                self.key_held_down = None

                if self.current_row == 0:
                    self.clear_api_field()
                    self.field = Field()
                    self.update_high_score(self.score)
                else:
                    self.make_api_move(cachedTetromino, self.current_rotation, self.current_col)
                    self.bestMove = self.best_api_move(self.current_tetromino)

                self.current_rotation = 0
                self.current_row = 0
                self.current_col = (self.field.cols // 2) - 2
            self.last_fall_time = current_time

        if self.key_held_down and shift_due:
            self.move_repeat_timer += current_time - self.last_shift_time
            while self.move_repeat_timer > self.arr_time / 1000.0:
                if self.key_held_down == 'Left':
                    self.move_left()
                elif self.key_held_down == 'Right':
                    self.move_right()
                self.move_repeat_timer -= self.arr_time / 1000.0
            self.last_shift_time = current_time

        self.update_grid()
        self.master.after(20, self.game_loop)

    def clear_api_field(self):
        headers = {
            'token': self.token,
        }
        request = requests.get(api + "/protected/clear-field", headers=headers)

    def make_api_move(self, tetromino, rotation, x):
        headers = {
            'token': self.token,
            'tetromino': tetromino.name,
            'rotation': str(rotation),
            'x': str(x)
        }
        request = requests.get(api + "/protected/update-field", headers=headers)

    def best_api_move(self, tetromino):
        headers = {
            'token': self.token,
            'tetromino': tetromino.name
        }
        request = requests.get(api + "/protected/best-move", headers=headers)
        move_data = json.loads(request.content.decode('utf-8'))
        return int(move_data['rotation'][0]), int(move_data['x'][0])

    def rotate(self, event=None):
        if not self.active:
            return
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
        if not self.active:
            return
        self.key_held_down = None

    def move_left(self, event=None):
        if not self.active:
            return
        if not self.field.check_collision(self.current_tetromino, self.current_rotation, self.current_row, self.current_col - 1):
            self.current_col -= 1
            self.update_grid()
            self.move_repeat_timer = 0  # Reset the repeat timer every time a move is made
            if event:  # If move is initiated by a keypress, reset the shift delay
                self.last_shift_time = time.time()

    def move_right(self, event=None):
        if not self.active:
            return
        if not self.field.check_collision(self.current_tetromino, self.current_rotation, self.current_row, self.current_col + 1):
            self.current_col += 1
            self.update_grid()
            self.move_repeat_timer = 0  # Reset the repeat timer every time a move is made
            if event:  # If move is initiated by a keypress, reset the shift delay
                self.last_shift_time = time.time()

    def reset_key_held_down(self, event=None):
        if not self.active:
            return
        self.key_held_down = None
        self.last_shift_time = time.time()  # Reset the last shift time when key is released
        self.move_repeat_timer = 0  # Reset the repeat timer when key is released

    def move_down(self, event=None):
        if not self.active:
            return
        if not self.field.check_collision(self.current_tetromino, self.current_rotation, self.current_row + 1,
                                          self.current_col):
            self.current_row += 1
            self.update_grid()

    def hard_drop(self, event=None):
        if not self.active:
            return
        while not self.field.check_collision(self.current_tetromino, self.current_rotation, self.current_row + 1,
                                             self.current_col):
            self.current_row += 1
        self.field.place_tetromino(self.current_tetromino, self.current_rotation, self.current_col)
        cachedTetromino = self.current_tetromino

        self.current_tetromino = self.next_tetrominoes.pop(0)
        self.next_tetrominoes.append(self.random_tetromino())
        self.draw_next_piece()
        self.score += 10

        self.key_held_down = None

        if self.current_row == 0:
            self.clear_api_field()
            self.field = Field()
            self.update_high_score(self.score)
        else:
            self.make_api_move(cachedTetromino, self.current_rotation, self.current_col)
            self.bestMove = self.best_api_move(self.current_tetromino)

        self.current_rotation = 0
        self.current_row = 0
        self.current_col = (self.field.cols // 2) - 2

    def click_window(self, event):
        # Record the initial position of the mouse when clicking the window
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def drag_window(self, event):
        # Calculate how much the mouse has moved
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]

        # Get the current position of the window
        x = self.canvas.winfo_rootx() + dx
        y = self.canvas.winfo_rooty() + dy

        # Move the window to the new position
        self.canvas.master.geometry(f"+{x}+{y}")

    def save_options_to_file(self, filename="options.json"):
        options = {
            "audio_enabled": self.audio_enabled,
            "das_time": self.das_time,
            "arr_time": self.arr_time,
            "difficulty": self.difficulty,
            "drop_time": self.drop_time
        }
        with open(filename, 'w') as file:
            json.dump(options, file, indent=4)