import time
import tkinter as tk
from tkinter import simpledialog, messagebox

import pygame
import requests
from PIL import ImageTk, ImageEnhance, Image

from tetris import TetrisApp

api = "http://localhost:6969"
token = "f2d955f0-7464-46fc-9390-f5138b263273"

# Dialog for sign up and login
class UserDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Username:").grid(row=0)
        tk.Label(master, text="Password:").grid(row=1)

        self.username = tk.Entry(master)
        self.password = tk.Entry(master, show="*")

        self.username.grid(row=0, column=1)
        self.password.grid(row=1, column=1)

        return self.username  # initial focus

    def apply(self):
        username = self.username.get()
        password = self.password.get()
        self.result = {"username": username, "password": password}


class TetrisMenu:
    def __init__(self, master):
        # Remove the title bar
        self.master = master
        master.overrideredirect(True)

        # Initialize pygame mixer
        pygame.init()
        pygame.mixer.init()

        # Load and play background music
        pygame.mixer.music.load("assets/background_music.wav")  # Change to your actual file path
        pygame.mixer.music.play(loops=-1)  # This will start the music and loop indefinitely

        master.geometry("1600x900")
        master.resizable(False, False)

        # Load images from the assets folder
        self.bg_image = tk.PhotoImage(file="assets/background.png")
        self.title_image = tk.PhotoImage(file="assets/title.png")
        self.start_button_image = tk.PhotoImage(file="assets/start_button.png")
        self.options_button_image = tk.PhotoImage(file="assets/options_button.png")
        self.exit_button_image = tk.PhotoImage(file="assets/exit_button.png")

        # Load hover sound
        self.hover_sound = pygame.mixer.Sound("assets/button_hover.mp3")
        # Load start sound
        self.start_sound = pygame.mixer.Sound("assets/start_game.mp3")

        # Background canvas
        self.canvas = tk.Canvas(master, width=1600, height=900, bd=0, highlightthickness=0, relief='flat')
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        self.canvas.images = []

        # Center the title image and move it down a bit (e.g., 150 pixels from the top)
        self.canvas.create_image(800, 150, image=self.title_image, anchor="center")

        # Make the window moveable
        self.canvas.bind("<Button-1>", self.click_window)
        self.canvas.bind("<B1-Motion>", self.drag_window)

        # Initial position
        self._drag_data = {"x": 0, "y": 0}

        # Buttons
        button_y_start_position = 350  # Starting Y position of the first button
        self.create_button(master, "Start", "assets/start_button.png", button_y_start_position)
        self.create_button(master, "Options", "assets/options_button.png", button_y_start_position + self.start_button_image.height() / 1.2)
        self.create_button(master, "Exit", "assets/exit_button.png", button_y_start_position + 2 * self.start_button_image.height() / 1.2)

    def create_button(self, master, text, image_path, y_position):
        # Use the ImageTk.PhotoImage to load the image directly
        tk_image = ImageTk.PhotoImage(file=image_path)

        # Create a canvas window to hold the button
        button_canvas = self.canvas.create_image(800, y_position, image=tk_image)

        # Bind mouse events to the canvas window
        self.canvas.tag_bind(button_canvas, "<Enter>", lambda e: self.on_hover(button_canvas, image_path, True, tk_image))
        self.canvas.tag_bind(button_canvas, "<Leave>", lambda e: self.on_hover(button_canvas, image_path, False, tk_image))
        self.canvas.tag_bind(button_canvas, "<Button-1>", lambda e: self.clicked(text))

        # Store a reference to the image to prevent garbage collection
        self.store_image(tk_image)

    def fade_to_black(self, duration=3000):
        # Create an overlay Toplevel window
        self.start_sound.play()
        self.overlay = tk.Toplevel(self.master)
        self.overlay.geometry("1600x900")  # Match the main window size
        self.overlay.overrideredirect(True)  # Remove window decorations
        self.overlay.attributes("-alpha", 0)  # Start completely transparent
        self.overlay.lift()  # Raise above the main window
        self.overlay.geometry(
            "+{}+{}".format(self.master.winfo_x(), self.master.winfo_y()))  # Position over the main window

        # Fill the overlay with a black background
        self.overlay.configure(bg='black')

        self.fade_in_step(0, duration)

    def fade_in_step(self, alpha, duration):
        steps = 100
        delta_alpha = 1.0 / steps
        interval = duration // steps

        if alpha < 1.0:
            alpha += delta_alpha
            self.overlay.attributes("-alpha", alpha)  # Gradually increase the opacity
            self.master.after(interval, lambda: self.fade_in_step(alpha, duration))
        else:
            pygame.mixer.music.stop()
            time.sleep(1)
            self.master.grab_release()
            TetrisApp(self.master, self.overlay, token)

    def clicked(self, button):
        match (button):
            case "Start":
                print(token)
                if token == "":
                    messagebox.showerror("Log In", "You must be logged in to play!")
                    return

                self.fade_to_black()
            case "Exit":
                quit()
            case "Options":
                self.show_login_signup_dialog()
                pass

    def on_hover(self, button_canvas, image_path, hover, tk_image):
        # The hover effect now needs to apply a tint to the tk_image directly
        if hover:
            self.hover_sound.play()
            # Apply a green tint effect to the tk_image
            self.apply_green_tint(image_path, button_canvas, True, tk_image)
        else:
            # Revert the button image to the original
            self.apply_green_tint(image_path, button_canvas, False, tk_image)

    # method for showing the sign-up/login dialog
    def show_login_signup_dialog(self):
        global token
        # Ask the user if they want to sign up or log in
        response = messagebox.askyesno("Sign Up/Login", "Would you like to sign up? (Press NO to log in)")
        if response:
            # Sign up process
            dialog = UserDialog(self.canvas.master, title="Sign Up")
            if dialog.result:
                signup_data = dialog.result
                headers = {
                    'identifier': signup_data.get("username"),
                    'password': signup_data.get("password"),
                }
                response = requests.get(api + "/register", headers=headers).json()
                if str(response["status"]) == "['success']":
                    messagebox.showinfo("Sign Up", "You have successfully signed up, you may now log in!")
                else:
                    messagebox.showinfo("Sign Up", "There is already somebody with your username signed up!")
        else:
            # Login process
            dialog = UserDialog(self.canvas.master, title="Log In")
            if dialog.result:
                login_data = dialog.result
                headers = {
                    'identifier': login_data.get("username"),
                    'password': login_data.get("password"),
                }
                response = requests.get(api + "/receive-auth", headers=headers).json()
                if str(response["status"]) == "['error']":
                    messagebox.showinfo("Log In", "Could not authenticate with your provided credentials!")
                else:
                    messagebox.showinfo("Log In", "You have successfully logged in and can play!")
                    token = str(response["status"]).removeprefix("['").removesuffix("']")

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

    def store_image(self, tk_image):
        # Store the Tkinter image reference to prevent garbage collection
        if not hasattr(self, 'images'):
            self.images = []
        self.images.append(tk_image)

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

if __name__ == '__main__':
    root = tk.Tk()
    app = TetrisMenu(root)
    root.mainloop()