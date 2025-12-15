import time
import tkinter as tk
from PIL import Image, ImageTk
import pygame
import ctypes
import os
import sys

# Get base path (works for .py and PyInstaller .exe)
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# Resource paths
SOUND_PATH = os.path.join(BASE_DIR, "assets/media/sounds/sound.mp3")
ICON_PATH = os.path.join(BASE_DIR, "assets/media/icons/shield_extrected.png")
IMAGE1_PATH = os.path.join(BASE_DIR, "assets/media/figures/1.png")       # Used for both startup and first reminder
IMAGE2_PATH = os.path.join(BASE_DIR, "assets/media/figures/2.png")       # Second reminder
IMAGE3_PATH = os.path.join(BASE_DIR, "assets/media/figures/3.png")       # Third reminder
IMAGE4_PATH = os.path.join(BASE_DIR, "assets/media/figures/4.png")       # Reserved if needed

# Initialize sound
pygame.init()
pygame.mixer.init()

def play_sound(repeat=1):
    for _ in range(repeat):
        pygame.mixer.music.load(SOUND_PATH)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

def show_popup(message, image_path):
    popup = tk.Tk()
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)

    # Get screen dimensions
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)

    popup_width = 420
    popup_height = 120
    x = screen_width - popup_width - 20
    y = screen_height - popup_height - 60
    popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

    # Outer border
    outer_frame = tk.Frame(popup, bg="black", bd=0)
    outer_frame.pack(fill="both", expand=True)

    # White inner frame
    container = tk.Frame(outer_frame, bg="white", padx=10, pady=10)
    container.pack(fill="both", expand=True)

    # Header
    header = tk.Frame(container, bg="#f0f0f0")
    header.pack(fill="x", pady=(0, 5))

    if os.path.exists(ICON_PATH):
        icon = Image.open(ICON_PATH).resize((20, 20))
        icon_photo = ImageTk.PhotoImage(icon)
        icon_label = tk.Label(header, image=icon_photo, bg="#f0f0f0")
        icon_label.image = icon_photo
        icon_label.pack(side="left", padx=(5, 5))

    title_label = tk.Label(
        header,
        text="EyeGuard • Developed by Ivan Sicaja © 2025 All rights reserved",
        font=("Calibri Light", 10),
        bg="#f0f0f0",
        fg="#2b2b2b"
    )
    title_label.pack(side="left")

    # Content
    content = tk.Frame(container, bg="white")
    content.pack(fill="both", expand=True)

    if os.path.exists(image_path):
        img = Image.open(image_path).resize((60, 60))
        photo = ImageTk.PhotoImage(img)
        img_label = tk.Label(content, image=photo, bg="white")
        img_label.image = photo
        img_label.pack(side="left", padx=10)

    message_label = tk.Label(
        content,
        text=message,
        font=("Calibri Light", 12),
        bg="white",
        fg="#2b7a2b",
        wraplength=280,
        justify="center"
    )
    message_label.pack(side="left", fill="both", expand=True)

    popup.after(5000, popup.destroy)
    popup.mainloop()

def main():
    # Startup popup
    show_popup("EyeGuard is now active — helping you care for your eyes!", image_path=IMAGE1_PATH)
    play_sound(1)

    while True:
        time.sleep(25 * 60)  # Wait 25 minutes

        # First reminder (30-second break)
        show_popup("Your eyes deserve a quick rest. Take a 30-second break!", image_path=IMAGE2_PATH)
        play_sound(1)

        time.sleep(30)

        # Second reminder (free time)
        show_popup("Eye break’s over. Enjoy 4½ minutes just for you!", image_path=IMAGE3_PATH)
        play_sound(1)

        time.sleep(4 * 60 + 30)

        # Third reminder (back to work)
        show_popup("Great! Let’s get back to it, refreshed and focused!", image_path=IMAGE4_PATH)
        play_sound(2)

if __name__ == "__main__":
    main()
