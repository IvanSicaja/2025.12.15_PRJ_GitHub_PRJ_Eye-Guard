import time
import tkinter as tk
from tkinter import Toplevel
from PIL import Image, ImageTk
import pygame
import ctypes
import os
import sys
import threading
import json
from queue import Queue

# ====================== BASE PATH ======================
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ====================== LOAD CONFIG ======================
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "config.json")

DEFAULT_CONFIG = {
    "work_time_min":   25,
    "work_time_sec":    0,
    "popup_opacity":  100,
    "test_mode":    False,
    "font_name":    "Montserrat",
    "message_color": "#222222",
    "popups": [
        {
            "trigger": "start",
            "message": "EyeGuard is now active — helping you care for your eyes!",
            "image": "1.png",
            "sound": "sound.mp3",
            "sound_repeat": 1
        },
        {
            "trigger": "work_end",
            "message": "Your eyes deserve a quick rest. Take a 30-second break!",
            "image": "2.png",
            "sound": "sound.mp3",
            "sound_repeat": 1
        },
        {
            "trigger": "break_end",
            "message": "Eye break's over. Enjoy 4½ minutes just for you!",
            "image": "3.png",
            "sound": "sound.mp3",
            "sound_repeat": 1,
            "duration_min": 0,
            "duration_sec": 30
        },
        {
            "trigger": "break_end",
            "message": "Great! Let's get back to it, refreshed and focused!",
            "image": "4.png",
            "sound": "sound.mp3",
            "sound_repeat": 2,
            "duration_min": 4,
            "duration_sec": 30
        }
    ]
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(user_cfg)
            return cfg
        except Exception as e:
            print(f"[CONFIG] Failed to load config.json, using defaults: {e}")
    return DEFAULT_CONFIG.copy()

CONFIG = load_config()

# ====================== CONFIGURATION ======================
MESSAGE_COLOR  = CONFIG.get("message_color", "#222222")
FONT_NAME      = CONFIG.get("font_name", "Montserrat")

# Popup opacity: value 10–100 (%) → alpha 0.10–1.00
_opacity_pct   = CONFIG.get("popup_opacity", 100)
POPUP_ALPHA    = max(0.10, min(1.0, _opacity_pct / 100.0))

ICON_PATH      = os.path.join(BASE_DIR, "assets", "media", "icons", "icon.png")
FIGURES_DIR    = os.path.join(BASE_DIR, "assets", "media", "figures")
SOUNDS_DIR     = os.path.join(BASE_DIR, "assets", "media", "sounds")

TEST_MODE = CONFIG.get("test_mode", False)

if TEST_MODE:
    WORK_TIME  = 5
else:
    WORK_TIME  = (CONFIG.get("work_time_min", 25) * 60
                  + CONFIG.get("work_time_sec", 0))

# Build the ordered list of break milestones from config
# Each break_end popup carries its own duration_min / duration_sec
BREAK_MILESTONES = [
    p for p in CONFIG.get("popups", [])
    if p.get("trigger") == "break_end"
]

# Total break time = sum of all milestone durations
BREAK_TIME = sum(
    p.get("duration_min", 0) * 60 + p.get("duration_sec", 0)
    for p in BREAK_MILESTONES
) if BREAK_MILESTONES else 0

TOTAL_CYCLE = WORK_TIME + BREAK_TIME

POPUPS = CONFIG.get("popups", DEFAULT_CONFIG["popups"])

def get_popup_by_trigger(trigger):
    """Return first popup matching trigger (used for start / work_end)."""
    for p in POPUPS:
        if p.get("trigger") == trigger:
            return p
    return None

pygame.init()
pygame.mixer.init()

def play_sound_async(sound_filename, repeat=1):
    sound_path = os.path.join(SOUNDS_DIR, sound_filename)
    def _play():
        for _ in range(repeat):
            if os.path.exists(sound_path):
                pygame.mixer.music.load(sound_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
    threading.Thread(target=_play, daemon=True).start()

popup_queue = Queue()
DISPLAY_TIME  = 3000

def fade_in(popup, target_alpha, step=0.0):
    """Fade in up to target_alpha (respects POPUP_ALPHA setting)."""
    if step <= target_alpha:
        popup.attributes("-alpha", step)
        popup.after(20, lambda: fade_in(popup, target_alpha, step + 0.05))
    else:
        popup.attributes("-alpha", target_alpha)

def fade_out(popup, step=None):
    if step is None:
        step = POPUP_ALPHA
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
    screen_width  = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    popup_width   = 420
    popup_height  = 160
    x = screen_width  - popup_width  - 20
    y = screen_height - popup_height - 60
    popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

    outer_frame = tk.Frame(popup, bg="black", bd=0)
    outer_frame.pack(fill="both", expand=True)

    container = tk.Frame(outer_frame, bg="white", padx=10, pady=10)
    container.pack(fill="both", expand=True)

    # Header
    header = tk.Frame(container, bg="white")
    header.pack(fill="x", pady=(0, 0))

    if os.path.exists(ICON_PATH):
        icon       = Image.open(ICON_PATH).resize((20, 20))
        icon_photo = ImageTk.PhotoImage(icon)
        popup.icon_photo = icon_photo
        tk.Label(header, image=icon_photo, bg="white").pack(side="left", padx=(5, 5))

    tk.Label(header, text="EyeGuard", font=(FONT_NAME, 10),
             bg="white", fg=MESSAGE_COLOR).pack(side="left")

    # Separator
    tk.Frame(container, height=1, bg="#dddddd").pack(fill="x", pady=(2, 5))

    # Content
    content = tk.Frame(container, bg="white")
    content.pack(fill="both", expand=True)

    if image_path and os.path.exists(image_path):
        img   = Image.open(image_path).resize((60, 60))
        photo = ImageTk.PhotoImage(img)
        popup.photo = photo
        tk.Label(content, image=photo, bg="white").pack(side="left", padx=10)

    tk.Label(content, text=message, font=(FONT_NAME, 12),
             bg="white", fg=MESSAGE_COLOR,
             wraplength=280, justify="center").pack(side="left", fill="both", expand=True)

    # Footer
    tk.Label(container,
             text="Developed by Ivan Sicaja © 2026. All rights reserved.",
             font=(FONT_NAME, 8), bg="white", fg="#555555"
             ).pack(side="bottom", pady=(5, 0))

    # Fade in to the configured opacity level, then fade out after display time
    fade_in(popup, POPUP_ALPHA)
    popup.after(DISPLAY_TIME + 1000, lambda: fade_out(popup, POPUP_ALPHA))

def show_popup(message, image_filename):
    image_path = os.path.join(FIGURES_DIR, image_filename) if image_filename else None
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

def fire_popup(trigger=None, popup_data=None):
    """Fire a popup either by trigger name or by passing a popup dict directly."""
    if popup_data is None and trigger is not None:
        popup_data = get_popup_by_trigger(trigger)
    if popup_data:
        show_popup(popup_data.get("message", ""), popup_data.get("image", ""))
        play_sound_async(
            popup_data.get("sound", "sound.mp3"),
            popup_data.get("sound_repeat", 1)
        )

def timer_thread():
    mode = "TEST" if TEST_MODE else "PRODUCTION"
    print(f"=== EyeGuard Starting in {mode} MODE ===")
    print(f"Work: {WORK_TIME}s | Break: {BREAK_TIME}s ({len(BREAK_MILESTONES)} milestones) "
          f"| Total: {TOTAL_CYCLE}s")
    print(f"Popup opacity: {_opacity_pct}%")
    print("=" * 60)

    fire_popup("start")

    cycle_number = 1
    while True:
        cycle_start = time.time()
        print(f"\n[CYCLE {cycle_number} START] {format_time_from_timestamp(cycle_start)}")

        # ── Work phase ──
        target = cycle_start + WORK_TIME
        time.sleep(max(0, target - time.time()))
        now = time.time()
        print(f"[WORK END] {format_time_from_timestamp(now)} | +{now - cycle_start:.3f}s")
        fire_popup("work_end")

        # ── Break phase — iterate through milestones in order ──
        milestone_start = time.time()
        for idx, milestone in enumerate(BREAK_MILESTONES):
            dur = (milestone.get("duration_min", 0) * 60
                   + milestone.get("duration_sec", 0))
            target = milestone_start + dur
            time.sleep(max(0, target - time.time()))
            milestone_start = time.time()   # next milestone starts from here
            now = time.time()
            print(f"[MILESTONE {idx + 1} END] {format_time_from_timestamp(now)} "
                  f"| +{now - cycle_start:.3f}s")
            fire_popup(popup_data=milestone)

        cycle_end = time.time()
        actual    = cycle_end - cycle_start
        drift     = actual - TOTAL_CYCLE
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