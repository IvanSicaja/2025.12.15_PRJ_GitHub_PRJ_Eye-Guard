"""
EyeGuard Configurator
Standalone configuration GUI for EyeGuard.
Run this script (or its EXE) from the same folder as main.py / main.exe.
It reads and writes config.json in that same folder.
"""

import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk

# ====================== PATHS ======================
SCRIPT_DIR  = os.path.dirname(os.path.abspath(sys.argv[0]))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIGURES_DIR = os.path.join(BASE_DIR, "assets", "media", "figures")
SOUNDS_DIR  = os.path.join(BASE_DIR, "assets", "media", "sounds")
ICON_PATH   = os.path.join(BASE_DIR, "assets", "media", "icons", "icon.png")

ALLOWED_IMAGE_EXTS = (".png", ".jpg", ".jpeg")
ALLOWED_SOUND_EXTS = (".mp3",)

TRIGGERS = ["start", "work_end", "break_end", "free_end"]
TRIGGER_LABELS = {
    "start":     "On Start",
    "work_end":  "Work End",
    "break_end": "Break End",
    "free_end":  "Free End",
}

DEFAULT_CONFIG = {
    "work_time":     25,
    "break_time":     3,
    "free_time":      2,
    "test_mode":  False,
    "font_name":  "Montserrat",
    "message_color": "#222222",
    "popups": [
        {"trigger": "start",      "message": "EyeGuard is now active — helping you care for your eyes!", "image": "1.png", "sound": "sound.mp3", "sound_repeat": 1},
        {"trigger": "work_end",   "message": "Your eyes deserve a quick rest. Take a 30-second break!",  "image": "2.png", "sound": "sound.mp3", "sound_repeat": 1},
        {"trigger": "break_end",  "message": "Eye break's over. Enjoy 4½ minutes just for you!",         "image": "3.png", "sound": "sound.mp3", "sound_repeat": 1},
        {"trigger": "free_end",   "message": "Great! Let's get back to it, refreshed and focused!",      "image": "4.png", "sound": "sound.mp3", "sound_repeat": 2},
    ]
}

# ====================== HELPERS ======================

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # Fill in any missing top-level keys from defaults
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not read config.json:\n{e}\n\nUsing defaults.")
    return json.loads(json.dumps(DEFAULT_CONFIG))   # deep copy

def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        messagebox.showerror("Save Error", f"Could not write config.json:\n{e}")
        return False

def list_figures():
    if not os.path.isdir(FIGURES_DIR):
        return []
    return sorted(
        f for f in os.listdir(FIGURES_DIR)
        if os.path.splitext(f)[1].lower() in ALLOWED_IMAGE_EXTS
    )

def list_sounds():
    if not os.path.isdir(SOUNDS_DIR):
        return []
    return sorted(
        f for f in os.listdir(SOUNDS_DIR)
        if os.path.splitext(f)[1].lower() in ALLOWED_SOUND_EXTS
    )

def get_popup(cfg, trigger):
    for p in cfg.get("popups", []):
        if p.get("trigger") == trigger:
            return p
    return {"trigger": trigger, "message": "", "image": "", "sound": "", "sound_repeat": 1}

# ====================== GUI ======================

class ConfigApp(tk.Tk):
    FONT_MAIN  = ("Segoe UI", 10)
    FONT_TITLE = ("Segoe UI Semibold", 11)
    FONT_HEAD  = ("Segoe UI Semibold", 13)
    BG         = "#f5f5f5"
    ACCENT     = "#1a73e8"
    PANEL      = "#ffffff"
    BORDER     = "#e0e0e0"
    FG         = "#222222"
    FG_LIGHT   = "#666666"

    def __init__(self):
        super().__init__()
        self.title("EyeGuard Configurator")
        self.resizable(False, False)
        self.configure(bg=self.BG)

        if os.path.exists(ICON_PATH):
            try:
                icon = ImageTk.PhotoImage(Image.open(ICON_PATH).resize((32, 32)))
                self.iconphoto(True, icon)
                self._icon_ref = icon
            except Exception:
                pass

        self.cfg = load_config()
        self._build_ui()
        self._populate()
        self.update_idletasks()
        # Centre on screen
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # UI BUILD
    # ------------------------------------------------------------------

    def _card(self, parent, title=None, **kwargs):
        outer = tk.Frame(parent, bg=self.BORDER, bd=0)
        inner = tk.Frame(outer, bg=self.PANEL, padx=16, pady=14)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        if title:
            tk.Label(inner, text=title, font=self.FONT_HEAD,
                     bg=self.PANEL, fg=self.FG).pack(anchor="w", pady=(0, 10))
        return outer, inner

    def _row(self, parent, label, widget_factory, **kw):
        row = tk.Frame(parent, bg=self.PANEL)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, font=self.FONT_MAIN,
                 bg=self.PANEL, fg=self.FG, width=18, anchor="w").pack(side="left")
        w = widget_factory(row, **kw)
        w.pack(side="left", fill="x", expand=True)
        return w

    def _spinbox(self, parent, from_=1, to=600, width=6, **kw):
        sb = tk.Spinbox(parent, from_=from_, to=to, width=width,
                        font=self.FONT_MAIN, relief="solid", bd=1,
                        highlightthickness=0, **kw)
        return sb

    def _combo(self, parent, values, width=28, **kw):
        style = ttk.Style()
        style.theme_use("clam")
        cb = ttk.Combobox(parent, values=values, width=width,
                          font=self.FONT_MAIN, state="readonly", **kw)
        return cb

    def _entry(self, parent, width=38, **kw):
        e = tk.Entry(parent, width=width, font=self.FONT_MAIN,
                     relief="solid", bd=1, highlightthickness=0, **kw)
        return e

    def _build_ui(self):
        pad = dict(padx=18, pady=8)

        # ── Title bar ──────────────────────────────────────────────────
        title_bar = tk.Frame(self, bg=self.ACCENT)
        title_bar.pack(fill="x")
        tk.Label(title_bar, text="  👁  EyeGuard Configurator",
                 font=("Segoe UI Semibold", 14), fg="white",
                 bg=self.ACCENT, pady=12).pack(side="left")
        tk.Label(title_bar,
                 text="config.json · " + SCRIPT_DIR,
                 font=("Segoe UI", 9), fg="#cce0ff",
                 bg=self.ACCENT, pady=12).pack(side="right", padx=14)

        # ── Main columns ───────────────────────────────────────────────
        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True, padx=18, pady=12)

        left  = tk.Frame(body, bg=self.BG)
        right = tk.Frame(body, bg=self.BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right.pack(side="left", fill="both", expand=True)

        # ── Timings ────────────────────────────────────────────────────
        card, pane = self._card(left, title="⏱  Timer Settings (minutes)")
        card.pack(fill="x", pady=(0, 10))

        self.var_work  = tk.StringVar()
        self.var_break = tk.StringVar()
        self.var_free  = tk.StringVar()

        self._row(pane, "Work Time",  self._spinbox, textvariable=self.var_work,  from_=1, to=240)
        self._row(pane, "Break Time", self._spinbox, textvariable=self.var_break, from_=1, to=60)
        self._row(pane, "Free Time",  self._spinbox, textvariable=self.var_free,  from_=1, to=60)

        self.var_test = tk.BooleanVar()
        row = tk.Frame(pane, bg=self.PANEL)
        row.pack(fill="x", pady=4)
        tk.Label(row, text="Test Mode (5 s)", font=self.FONT_MAIN,
                 bg=self.PANEL, fg=self.FG, width=18, anchor="w").pack(side="left")
        tk.Checkbutton(row, variable=self.var_test,
                       bg=self.PANEL, activebackground=self.PANEL,
                       relief="flat").pack(side="left")

        # ── Appearance ────────────────────────────────────────────────
        card2, pane2 = self._card(left, title="🎨  Appearance")
        card2.pack(fill="x", pady=(0, 10))

        self.var_font  = tk.StringVar()
        self.var_color = tk.StringVar()

        self._row(pane2, "Font Name",  self._entry,  textvariable=self.var_font,  width=26)
        self._row(pane2, "Text Color", self._entry,  textvariable=self.var_color, width=26)
        tk.Label(pane2, text="Use hex color codes, e.g. #222222",
                 font=("Segoe UI", 8), bg=self.PANEL, fg=self.FG_LIGHT
                 ).pack(anchor="w", padx=(140, 0))

        # ── Available Assets ──────────────────────────────────────────
        card3, pane3 = self._card(left, title="📁  Available Assets")
        card3.pack(fill="x")

        self._asset_figures_lbl = tk.Label(pane3, font=self.FONT_MAIN,
                                           bg=self.PANEL, fg=self.FG_LIGHT,
                                           justify="left", wraplength=320)
        self._asset_figures_lbl.pack(anchor="w")
        self._asset_sounds_lbl  = tk.Label(pane3, font=self.FONT_MAIN,
                                           bg=self.PANEL, fg=self.FG_LIGHT,
                                           justify="left", wraplength=320)
        self._asset_sounds_lbl.pack(anchor="w", pady=(4, 0))
        tk.Label(pane3,
                 text="Place new images in assets/media/figures\nPlace new sounds in assets/media/sounds",
                 font=("Segoe UI", 8), bg=self.PANEL, fg="#999999"
                 ).pack(anchor="w", pady=(6, 0))

        # ── Popup Events ──────────────────────────────────────────────
        card4, pane4 = self._card(right, title="💬  Popup Events")
        card4.pack(fill="both", expand=True)

        self._popup_frames = {}
        figures = list_figures()
        sounds  = list_sounds()

        for trigger in TRIGGERS:
            section = tk.LabelFrame(pane4,
                                    text=f"  {TRIGGER_LABELS[trigger]}  ",
                                    font=self.FONT_TITLE,
                                    bg=self.PANEL, fg=self.ACCENT,
                                    relief="groove", bd=1,
                                    padx=10, pady=8)
            section.pack(fill="x", pady=(0, 10))

            # Message
            msg_row = tk.Frame(section, bg=self.PANEL)
            msg_row.pack(fill="x", pady=3)
            tk.Label(msg_row, text="Message", font=self.FONT_MAIN,
                     bg=self.PANEL, fg=self.FG, width=14, anchor="w").pack(side="left")
            var_msg = tk.StringVar()
            ent = tk.Entry(msg_row, textvariable=var_msg, width=42,
                           font=self.FONT_MAIN, relief="solid", bd=1,
                           highlightthickness=0)
            ent.pack(side="left", fill="x", expand=True)

            # Image
            img_row = tk.Frame(section, bg=self.PANEL)
            img_row.pack(fill="x", pady=3)
            tk.Label(img_row, text="Image", font=self.FONT_MAIN,
                     bg=self.PANEL, fg=self.FG, width=14, anchor="w").pack(side="left")
            var_img = tk.StringVar()
            cb_img = ttk.Combobox(img_row, textvariable=var_img,
                                  values=figures, width=20,
                                  font=self.FONT_MAIN, state="normal")
            cb_img.pack(side="left")

            # Preview thumbnail
            preview_lbl = tk.Label(img_row, bg=self.PANEL)
            preview_lbl.pack(side="left", padx=(8, 0))

            def _make_preview_updater(lbl, sv):
                def _update(*_):
                    fn = sv.get()
                    path = os.path.join(FIGURES_DIR, fn)
                    if os.path.exists(path):
                        try:
                            img   = Image.open(path).resize((32, 32))
                            photo = ImageTk.PhotoImage(img)
                            lbl.config(image=photo)
                            lbl._photo = photo
                        except Exception:
                            lbl.config(image="")
                    else:
                        lbl.config(image="")
                return _update

            updater = _make_preview_updater(preview_lbl, var_img)
            var_img.trace_add("write", updater)

            # Sound
            snd_row = tk.Frame(section, bg=self.PANEL)
            snd_row.pack(fill="x", pady=3)
            tk.Label(snd_row, text="Sound", font=self.FONT_MAIN,
                     bg=self.PANEL, fg=self.FG, width=14, anchor="w").pack(side="left")
            var_snd = tk.StringVar()
            cb_snd = ttk.Combobox(snd_row, textvariable=var_snd,
                                  values=sounds, width=20,
                                  font=self.FONT_MAIN, state="normal")
            cb_snd.pack(side="left")

            # Repeat
            tk.Label(snd_row, text="  Repeat", font=self.FONT_MAIN,
                     bg=self.PANEL, fg=self.FG).pack(side="left")
            var_rep = tk.StringVar()
            tk.Spinbox(snd_row, from_=1, to=10, width=4,
                       textvariable=var_rep,
                       font=self.FONT_MAIN, relief="solid", bd=1,
                       highlightthickness=0).pack(side="left", padx=(4, 0))

            self._popup_frames[trigger] = {
                "message":      var_msg,
                "image":        var_img,
                "sound":        var_snd,
                "sound_repeat": var_rep,
            }

        # ── Buttons ───────────────────────────────────────────────────
        btn_bar = tk.Frame(self, bg=self.BG)
        btn_bar.pack(fill="x", padx=18, pady=(0, 14))

        btn_style = dict(font=("Segoe UI Semibold", 10),
                         relief="flat", cursor="hand2",
                         padx=20, pady=8, bd=0)

        tk.Button(btn_bar, text="↺  Reset to Defaults",
                  bg="#eeeeee", fg=self.FG,
                  command=self._reset,
                  **btn_style).pack(side="left")

        tk.Button(btn_bar, text="✔  Save Configuration",
                  bg=self.ACCENT, fg="white",
                  activebackground="#1558b0", activeforeground="white",
                  command=self._save,
                  **btn_style).pack(side="right")

        # footer
        tk.Label(self,
                 text="Developed by Ivan Sicaja © 2026. All rights reserved.",
                 font=("Segoe UI", 8), bg=self.BG, fg="#aaaaaa"
                 ).pack(pady=(0, 6))

    # ------------------------------------------------------------------
    # POPULATE / SAVE / RESET
    # ------------------------------------------------------------------

    def _populate(self):
        self.var_work.set(str(self.cfg.get("work_time",  25)))
        self.var_break.set(str(self.cfg.get("break_time", 3)))
        self.var_free.set(str(self.cfg.get("free_time",   2)))
        self.var_test.set(self.cfg.get("test_mode", False))
        self.var_font.set(self.cfg.get("font_name", "Montserrat"))
        self.var_color.set(self.cfg.get("message_color", "#222222"))

        figures = list_figures()
        sounds  = list_sounds()
        fig_str = "Images: " + (", ".join(figures) if figures else "none found")
        snd_str = "Sounds: " + (", ".join(sounds)  if sounds  else "none found")
        self._asset_figures_lbl.config(text=fig_str)
        self._asset_sounds_lbl.config(text=snd_str)

        for trigger, widgets in self._popup_frames.items():
            popup = get_popup(self.cfg, trigger)
            widgets["message"].set(popup.get("message", ""))
            widgets["image"].set(popup.get("image", ""))
            widgets["sound"].set(popup.get("sound", ""))
            widgets["sound_repeat"].set(str(popup.get("sound_repeat", 1)))

    def _collect(self):
        """Read all widgets into a config dict."""
        try:
            work  = int(self.var_work.get())
            brk   = int(self.var_break.get())
            free  = int(self.var_free.get())
        except ValueError:
            messagebox.showerror("Validation Error",
                                 "Work / Break / Free times must be whole numbers.")
            return None

        popups = []
        for trigger, widgets in self._popup_frames.items():
            try:
                repeat = int(widgets["sound_repeat"].get())
            except ValueError:
                repeat = 1
            popups.append({
                "trigger":      trigger,
                "message":      widgets["message"].get().strip(),
                "image":        widgets["image"].get().strip(),
                "sound":        widgets["sound"].get().strip(),
                "sound_repeat": max(1, repeat),
            })

        return {
            "work_time":     work,
            "break_time":    brk,
            "free_time":     free,
            "test_mode":     self.var_test.get(),
            "font_name":     self.var_font.get().strip(),
            "message_color": self.var_color.get().strip(),
            "popups":        popups,
        }

    def _save(self):
        cfg = self._collect()
        if cfg is None:
            return
        if save_config(cfg):
            self.cfg = cfg
            messagebox.showinfo("Saved",
                                f"Configuration saved to:\n{CONFIG_PATH}\n\n"
                                "Restart EyeGuard for changes to take effect.")

    def _reset(self):
        if messagebox.askyesno("Reset", "Reset all settings to defaults?"):
            self.cfg = json.loads(json.dumps(DEFAULT_CONFIG))
            self._populate()

# ====================== ENTRY ======================

if __name__ == "__main__":
    app = ConfigApp()
    app.mainloop()