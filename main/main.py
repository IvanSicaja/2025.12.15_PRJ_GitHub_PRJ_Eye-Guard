import time
import tkinter as tk
from tkinter import Toplevel
from PIL import Image, ImageTk
import pygame
import ctypes
import os
import sys
import threading
from queue import Queue

# ====================== CONFIGURATION ======================
MESSAGE_COLOR = "#000000"  # popup message color
FONT_NAME = "Montserrat"   # "Montserrat"   or "Garrett Book"

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOUND_PATH = os.path.join(BASE_DIR, "assets", "media", "sounds", "sound.mp3")
ICON_PATH = os.path.join(BASE_DIR, "assets", "media", "icons", "icon.png")
IMAGE1_PATH = os.path.join(BASE_DIR, "assets", "media", "figures", "1.png")
IMAGE2_PATH = os.path.join(BASE_DIR, "assets", "media", "figures", "2.png")
IMAGE3_PATH = os.path.join(BASE_DIR, "assets", "media", "figures", "3.png")
IMAGE4_PATH = os.path.join(BASE_DIR, "assets", "media", "figures", "4.png")

TEST_MODE = True
if TEST_MODE:
    WORK_TIME = 5
    BREAK_TIME = 5
    FREE_TIME = 5
else:
    WORK_TIME = 25 * 60
    BREAK_TIME = 30
    FREE_TIME = 4 * 60 + 30
TOTAL_CYCLE = WORK_TIME + BREAK_TIME + FREE_TIME

pygame.init()
pygame.mixer.init()

def play_sound_async(repeat=1):
    def _play():
        for _ in range(repeat):
            pygame.mixer.music.load(SOUND_PATH)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
    threading.Thread(target=_play, daemon=True).start()

popup_queue = Queue()
FADE_DURATION = 1000
DISPLAY_TIME = 3000

def fade_in(popup, step=0.0):
    if step <= 1.0:
        popup.attributes("-alpha", step)
        popup.after(20, lambda: fade_in(popup, step + 0.05))
    else:
        popup.attributes("-alpha", 1.0)

def fade_out(popup, step=1.0):
    if step >= 0.0:
        popup.attributes("-alpha", step)
        popup.after(20, lambda: fade_out(popup, step - 0.05))
    else:
        popup.attributes("-alpha", 0.0)
        popup.destroy()

def create_popup(root, message, image_path):
    popup = Toplevel(root)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup.attributes("-alpha", 0.0)

    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    popup_width = 420
    popup_height = 140
    x = screen_width - popup_width - 20
    y = screen_height - popup_height - 60
    popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

    outer_frame = tk.Frame(popup, bg="black", bd=0)
    outer_frame.pack(fill="both", expand=True)

    container = tk.Frame(outer_frame, bg="white", padx=10, pady=10)
    container.pack(fill="both", expand=True)

    header = tk.Frame(container, bg="#f0f0f0")
    header.pack(fill="x", pady=(0, 5))

    if os.path.exists(ICON_PATH):
        icon = Image.open(ICON_PATH).resize((20, 20))
        icon_photo = ImageTk.PhotoImage(icon)
        popup.icon_photo = icon_photo
        tk.Label(header, image=icon_photo, bg="#f0f0f0").pack(side="left", padx=(5, 5))

    # ------------ Header Text Fixed Size (previous size, not bold) ------------
    title_label = tk.Label(
        header,
        text="EyeGuard",
        font=(FONT_NAME, 10),  # previous size
        bg="#f0f0f0",
        fg="#2b2b2b"
    )
    title_label.pack(side="left")

    content = tk.Frame(container, bg="white")
    content.pack(fill="both", expand=True)

    if os.path.exists(image_path):
        img = Image.open(image_path).resize((60, 60))
        photo = ImageTk.PhotoImage(img)
        popup.photo = photo
        tk.Label(content, image=photo, bg="white").pack(side="left", padx=10)

    message_label = tk.Label(
        content,
        text=message,
        font=(FONT_NAME, 12),
        bg="white",
        fg=MESSAGE_COLOR,
        wraplength=280,
        justify="center"
    )
    message_label.pack(side="left", fill="both", expand=True)

    footer = tk.Label(
        container,
        text="Developed by Ivan Sicaja © 2026. All rights reserved.",
        font=(FONT_NAME, 8),
        bg="white",
        fg="#555555"
    )
    footer.pack(side="bottom", pady=(5,0))

    fade_in(popup)
    popup.after(DISPLAY_TIME + 1000, lambda: fade_out(popup))

def show_popup(message, image_path):
    popup_queue.put((message, image_path))

def check_popup_queue(root):
    try:
        while not popup_queue.empty():
            message, image_path = popup_queue.get_nowait()
            create_popup(root, message, image_path)
    except:
        pass
    root.after(100, lambda: check_popup_queue(root))

def format_time_from_timestamp(timestamp):
    return time.strftime('%H:%M:%S', time.localtime(timestamp)) + f".{int(timestamp % 1 * 1000):03d}"

def timer_thread():
    mode = "TEST" if TEST_MODE else "PRODUCTION"
    print(f"=== EyeGuard Starting in {mode} MODE ===")
    print(f"Work: {WORK_TIME}s | Break: {BREAK_TIME}s | Free: {FREE_TIME}s | Total: {TOTAL_CYCLE}s")
    print("=" * 60)

    show_popup("EyeGuard is now active — helping you care for your eyes!", image_path=IMAGE1_PATH)
    play_sound_async(1)

    cycle_number = 1
    while True:
        cycle_start = time.time()
        print(f"\n[CYCLE {cycle_number} START] {format_time_from_timestamp(cycle_start)}")

        target = cycle_start + WORK_TIME
        time.sleep(max(0, target - time.time()))
        now = time.time()
        print(f"[WORK END / BEEP] {format_time_from_timestamp(now)} | +{now - cycle_start:.3f}s")
        show_popup("Your eyes deserve a quick rest. Take a 30-second break!", image_path=IMAGE2_PATH)
        play_sound_async(1)

        target = cycle_start + WORK_TIME + BREAK_TIME
        time.sleep(max(0, target - time.time()))
        now = time.time()
        print(f"[BREAK END / BEEP] {format_time_from_timestamp(now)} | +{now - cycle_start:.3f}s")
        show_popup("Eye break’s over. Enjoy 4½ minutes just for you!", image_path=IMAGE3_PATH)
        play_sound_async(1)

        target = cycle_start + WORK_TIME + BREAK_TIME + FREE_TIME
        time.sleep(max(0, target - time.time()))
        now = time.time()
        print(f"[FREE END / BEEP] {format_time_from_timestamp(now)} | +{now - cycle_start:.3f}s")
        show_popup("Great! Let’s get back to it, refreshed and focused!", image_path=IMAGE4_PATH)
        play_sound_async(2)

        cycle_end = time.time()
        actual = cycle_end - cycle_start
        drift = actual - TOTAL_CYCLE
        print(
            f"[CYCLE {cycle_number} END] {format_time_from_timestamp(cycle_end)} | "
            f"Expected: {TOTAL_CYCLE:.3f}s | Actual: {actual:.3f}s | Drift: {drift:+.3f}s"
        )
        cycle_number += 1

def main():
    root = tk.Tk()
    root.withdraw()
    check_popup_queue(root)
    threading.Thread(target=timer_thread, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main()
