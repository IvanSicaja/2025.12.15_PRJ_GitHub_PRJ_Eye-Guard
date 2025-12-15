import time
import tkinter as tk
from tkinter import Toplevel
from PIL import Image, ImageTk
from playsound import playsound
import ctypes
import os
import sys
import threading
from queue import Queue

# Get base path (works for .py and PyInstaller .exe)
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = sys._MEIPASS
else:
    # Running as script - go up one level from main folder to root
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Resource paths
SOUND_PATH = os.path.join(BASE_DIR, "assets", "media", "sounds", "sound.mp3")
ICON_PATH = os.path.join(BASE_DIR, "assets", "media", "icons", "shield_extrected.png")
IMAGE1_PATH = os.path.join(BASE_DIR, "assets", "media", "figures", "1.png")
IMAGE2_PATH = os.path.join(BASE_DIR, "assets", "media", "figures", "2.png")
IMAGE3_PATH = os.path.join(BASE_DIR, "assets", "media", "figures", "3.png")
IMAGE4_PATH = os.path.join(BASE_DIR, "assets", "media", "figures", "4.png")

# ============================================================================
# TIMING CONFIGURATION - Change these values as needed
# ============================================================================

# TEST MODE: Set to True for quick 5-second testing, False for production
TEST_MODE = True

if TEST_MODE:
    # Test timings (in seconds) - for quick testing
    WORK_TIME = 5  # Time before first reminder (5 seconds)
    BREAK_TIME = 5  # Eye break duration (5 seconds)
    FREE_TIME = 5  # Free time after break (5 seconds)
    TOTAL_CYCLE = WORK_TIME + BREAK_TIME + FREE_TIME  # 15 seconds total
else:
    # Production timings (in seconds) - for actual use
    WORK_TIME = 25 * 60  # 25 minutes before first reminder
    BREAK_TIME = 30  # 30-second eye break
    FREE_TIME = 4 * 60 + 30  # 4.5 minutes free time
    TOTAL_CYCLE = 30 * 60  # 30 minutes total cycle

# ============================================================================

# Global queue for popup requests
popup_queue = Queue()


def play_sound_async(repeat=1):
    """Play sound in a separate thread so it doesn't block timing"""

    def _play():
        for _ in range(repeat):
            playsound(SOUND_PATH)

    thread = threading.Thread(target=_play, daemon=True)
    thread.start()


def create_popup(root, message, image_path):
    """Create popup window (called from main thread)"""
    popup = Toplevel(root)
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
        popup.icon_photo = icon_photo  # Keep reference
        icon_label = tk.Label(header, image=icon_photo, bg="#f0f0f0")
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
        popup.photo = photo  # Keep reference
        img_label = tk.Label(content, image=photo, bg="white")
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


def show_popup(message, image_path):
    """Queue a popup to be shown by the main thread"""
    popup_queue.put((message, image_path))


def check_popup_queue(root):
    """Check for pending popups and create them"""
    try:
        while not popup_queue.empty():
            message, image_path = popup_queue.get_nowait()
            create_popup(root, message, image_path)
    except:
        pass

    # Check again in 100ms
    root.after(100, lambda: check_popup_queue(root))


def timer_thread():
    """Run the timer in a separate thread"""
    mode = "TEST" if TEST_MODE else "PRODUCTION"
    print(f"=== EyeGuard Starting in {mode} MODE ===")
    print(f"Base directory: {BASE_DIR}")
    print(f"Sound path: {SOUND_PATH}")
    print(f"Sound exists: {os.path.exists(SOUND_PATH)}")
    print(f"Work time: {WORK_TIME}s | Break time: {BREAK_TIME}s | Free time: {FREE_TIME}s")
    print(f"Total cycle: {TOTAL_CYCLE}s")
    print(f"Started at: {time.strftime('%H:%M:%S')}")
    print("=" * 50)

    # Startup popup
    show_popup("EyeGuard is now active — helping you care for your eyes!", image_path=IMAGE1_PATH)
    play_sound_async(1)

    # Record start time for precise timing
    cycle_start = time.time()
    cycle_number = 1

    while True:
        # Wait exactly WORK_TIME from cycle start
        target_time = cycle_start + WORK_TIME
        time.sleep(max(0, target_time - time.time()))

        # First reminder - 30-second break
        current_time = time.strftime('%H:%M:%S')
        print(
            f"[Cycle {cycle_number}] Reminder 1 at {current_time} (expected: {time.strftime('%H:%M:%S', time.localtime(target_time))})")
        show_popup("Your eyes deserve a quick rest. Take a 30-second break!", image_path=IMAGE2_PATH)
        play_sound_async(1)

        # Wait exactly BREAK_TIME
        target_time = cycle_start + WORK_TIME + BREAK_TIME
        time.sleep(max(0, target_time - time.time()))

        # Second reminder - free time
        current_time = time.strftime('%H:%M:%S')
        print(
            f"[Cycle {cycle_number}] Reminder 2 at {current_time} (expected: {time.strftime('%H:%M:%S', time.localtime(target_time))})")
        show_popup("Eye break's over. Enjoy 4½ minutes just for you!", image_path=IMAGE3_PATH)
        play_sound_async(1)

        # Wait exactly FREE_TIME
        target_time = cycle_start + WORK_TIME + BREAK_TIME + FREE_TIME
        time.sleep(max(0, target_time - time.time()))

        # Third reminder - back to work
        current_time = time.strftime('%H:%M:%S')
        print(
            f"[Cycle {cycle_number}] Reminder 3 at {current_time} (expected: {time.strftime('%H:%M:%S', time.localtime(target_time))})")
        show_popup("Great! Let's get back to it, refreshed and focused!", image_path=IMAGE4_PATH)
        play_sound_async(2)

        print(
            f"[Cycle {cycle_number}] Complete. Next cycle starts in {TOTAL_CYCLE - (WORK_TIME + BREAK_TIME + FREE_TIME)}s")
        print("-" * 50)

        # Move to next cycle
        cycle_start += TOTAL_CYCLE
        cycle_number += 1


def main():
    # Create hidden root window
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Start checking for popup requests
    check_popup_queue(root)

    # Start timer in background thread
    thread = threading.Thread(target=timer_thread, daemon=True)
    thread.start()

    # Run tkinter main loop
    root.mainloop()


if __name__ == "__main__":
    main()