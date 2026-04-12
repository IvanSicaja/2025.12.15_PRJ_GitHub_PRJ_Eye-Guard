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

# Fixed triggers rendered before and after break milestones
FIXED_TRIGGERS_BEFORE = ["start", "work_end"]
FIXED_TRIGGERS_AFTER  = ["free_end"]
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
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not read config.json:\n{e}\n\nUsing defaults.")
    return json.loads(json.dumps(DEFAULT_CONFIG))

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

def get_break_milestones(cfg):
    """Return all break_end popups from config in their saved order."""
    return [p for p in cfg.get("popups", []) if p.get("trigger") == "break_end"]


# ====================== BREAK MILESTONE MANAGER ======================

class BreakMilestoneManager:
    """
    Renders break milestone entries directly into a given parent frame
    (the shared scroll_frame). No inner canvas/scrollbar — the parent
    handles scrolling. Supports add, delete, move up/down.
    """

    PANEL      = "#ffffff"
    ACCENT     = "#1a73e8"
    FG         = "#222222"
    FG_LIGHT   = "#666666"
    BORDER     = "#e0e0e0"
    FONT_MAIN  = ("Segoe UI", 10)
    FONT_TITLE = ("Segoe UI Semibold", 11)

    def __init__(self, parent, figures, sounds,
                 divider_widget, after_widgets):
        """
        parent         – the scroll_frame to pack into
        figures        – list of image filenames
        sounds         – list of sound filenames
        divider_widget – the tk.Frame divider that must always stay after milestones
        after_widgets  – list of tk widgets (free_end section) that must stay after divider
        """
        self.parent         = parent
        self.figures        = figures
        self.sounds         = sounds
        self._divider       = divider_widget
        self._after_widgets = after_widgets
        self._entries       = []

        self._build_header()

        self._empty_label = tk.Label(
            self.parent,
            text="No break milestones yet. Click '＋ Add Milestone' to create one.",
            font=("Segoe UI", 9),
            bg=self.PANEL, fg="#aaaaaa",
            justify="center"
        )

    def _build_header(self):
        self._header = tk.Frame(self.parent, bg=self.PANEL)
        self._header.pack(fill="x", padx=2, pady=(4, 4))

        accent_bar = tk.Frame(self._header, bg=self.ACCENT, width=4)
        accent_bar.pack(side="left", fill="y", padx=(0, 8))

        tk.Label(
            self._header,
            text="🔔  Break Milestone Popups",
            font=("Segoe UI Semibold", 11),
            bg=self.PANEL, fg=self.FG
        ).pack(side="left")

        tk.Label(
            self._header,
            text="(triggered sequentially during break)",
            font=("Segoe UI", 8),
            bg=self.PANEL, fg=self.FG_LIGHT
        ).pack(side="left", padx=(8, 0))

        add_btn = tk.Button(
            self._header,
            text="＋  Add Milestone",
            font=("Segoe UI Semibold", 9),
            bg=self.ACCENT, fg="white",
            activebackground="#1558b0", activeforeground="white",
            relief="flat", cursor="hand2",
            padx=10, pady=3, bd=0,
            command=self._add_entry
        )
        add_btn.pack(side="right", padx=(0, 2))

    # ------------------------------------------------------------------

    def _add_entry(self, data=None):
        if data is None:
            data = {"message": "", "image": "", "sound": "", "sound_repeat": 1}

        entry = {
            "message":      tk.StringVar(value=data.get("message", "")),
            "image":        tk.StringVar(value=data.get("image", "")),
            "sound":        tk.StringVar(value=data.get("sound", "")),
            "sound_repeat": tk.StringVar(value=str(data.get("sound_repeat", 1))),
            "frame":        None,
            "_idx_label":   None,
        }

        frame = self._build_entry_frame(entry)
        entry["frame"] = frame
        self._entries.append(entry)
        self._repack()

    def _build_entry_frame(self, entry):
        frame = tk.Frame(self.parent, bg=self.PANEL)

        card = tk.Frame(frame, bg="#f0f4ff", relief="flat", bd=0,
                        highlightbackground="#c5d5f5", highlightthickness=1)
        card.pack(fill="x", padx=6, pady=3, ipady=5, ipadx=8)

        # Top row
        top_row = tk.Frame(card, bg="#f0f4ff")
        top_row.pack(fill="x", pady=(0, 4))

        idx_lbl = tk.Label(top_row, text="", font=("Segoe UI Semibold", 9),
                           bg="#f0f4ff", fg=self.ACCENT)
        idx_lbl.pack(side="left")
        entry["_idx_label"] = idx_lbl

        btn_cfg = dict(font=("Segoe UI", 9), relief="flat", cursor="hand2",
                       padx=6, pady=2, bd=0)

        btn_frame = tk.Frame(top_row, bg="#f0f4ff")
        btn_frame.pack(side="right")

        tk.Button(btn_frame, text="▲", bg="#e8e8e8", fg=self.FG,
                  **btn_cfg,
                  command=lambda: self._move_entry(entry, -1)).pack(side="left", padx=2)
        tk.Button(btn_frame, text="▼", bg="#e8e8e8", fg=self.FG,
                  **btn_cfg,
                  command=lambda: self._move_entry(entry, +1)).pack(side="left", padx=2)
        tk.Button(btn_frame, text="✕  Delete", bg="#ffeded", fg="#cc0000",
                  activebackground="#ffcccc", activeforeground="#990000",
                  **btn_cfg,
                  command=lambda: self._delete_entry(entry)).pack(side="left", padx=(6, 0))

        # Message
        r_msg = tk.Frame(card, bg="#f0f4ff")
        r_msg.pack(fill="x", pady=2)
        tk.Label(r_msg, text="Message", font=self.FONT_MAIN, bg="#f0f4ff",
                 fg=self.FG, width=14, anchor="w").pack(side="left")
        tk.Entry(r_msg, textvariable=entry["message"], width=42,
                 font=self.FONT_MAIN, relief="solid", bd=1,
                 highlightthickness=0).pack(side="left", fill="x", expand=True)

        # Image
        r_img = tk.Frame(card, bg="#f0f4ff")
        r_img.pack(fill="x", pady=2)
        tk.Label(r_img, text="Image", font=self.FONT_MAIN, bg="#f0f4ff",
                 fg=self.FG, width=14, anchor="w").pack(side="left")
        ttk.Combobox(r_img, textvariable=entry["image"],
                     values=self.figures, width=20,
                     font=self.FONT_MAIN, state="normal").pack(side="left")

        preview_lbl = tk.Label(r_img, bg="#f0f4ff")
        preview_lbl.pack(side="left", padx=(8, 0))

        def _make_updater(lbl, sv):
            def _update(*_):
                path = os.path.join(FIGURES_DIR, sv.get())
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

        updater = _make_updater(preview_lbl, entry["image"])
        entry["image"].trace_add("write", updater)
        updater()

        # Sound + Repeat
        r_snd = tk.Frame(card, bg="#f0f4ff")
        r_snd.pack(fill="x", pady=2)
        tk.Label(r_snd, text="Sound", font=self.FONT_MAIN, bg="#f0f4ff",
                 fg=self.FG, width=14, anchor="w").pack(side="left")
        ttk.Combobox(r_snd, textvariable=entry["sound"],
                     values=self.sounds, width=20,
                     font=self.FONT_MAIN, state="normal").pack(side="left")
        tk.Label(r_snd, text="  Repeat", font=self.FONT_MAIN,
                 bg="#f0f4ff", fg=self.FG).pack(side="left")
        tk.Spinbox(r_snd, from_=1, to=10, width=4,
                   textvariable=entry["sound_repeat"],
                   font=self.FONT_MAIN, relief="solid", bd=1,
                   highlightthickness=0).pack(side="left", padx=(4, 0))

        return frame

    def _delete_entry(self, entry):
        self._entries.remove(entry)
        entry["frame"].destroy()
        self._repack()

    def _move_entry(self, entry, direction):
        idx = self._entries.index(entry)
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self._entries):
            return
        self._entries[idx], self._entries[new_idx] = self._entries[new_idx], self._entries[idx]
        self._repack()

    def _repack(self):
        """
        Re-pack everything in the correct order:
          header → [entries in order] (or empty label) → divider → after_widgets
        """
        # Unpack all managed widgets
        self._empty_label.pack_forget()
        for e in self._entries:
            e["frame"].pack_forget()
        self._divider.pack_forget()
        for w in self._after_widgets:
            w.pack_forget()

        # Re-pack entries (or empty label)
        if not self._entries:
            self._empty_label.pack(fill="x", padx=8, pady=6)
        else:
            for i, e in enumerate(self._entries):
                e["frame"].pack(fill="x")
                e["_idx_label"].config(text=f"Milestone #{i + 1}")

        # Divider
        self._divider.pack(fill="x", pady=(6, 6), padx=2)

        # After-widgets (free_end section)
        for w in self._after_widgets:
            w.pack(fill="x", pady=(0, 8), padx=2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_milestones(self, milestone_list):
        """Load milestones in the exact order given. Clears any existing ones first."""
        for e in list(self._entries):
            e["frame"].destroy()
        self._entries.clear()
        self._empty_label.pack_forget()

        for data in milestone_list:
            self._add_entry(data)

        # _add_entry calls _repack each time; final state is correct after loop.

    def collect_milestones(self):
        """Return milestones in current display order."""
        result = []
        for e in self._entries:
            try:
                repeat = int(e["sound_repeat"].get())
            except ValueError:
                repeat = 1
            result.append({
                "trigger":      "break_end",
                "message":      e["message"].get().strip(),
                "image":        e["image"].get().strip(),
                "sound":        e["sound"].get().strip(),
                "sound_repeat": max(1, repeat),
            })
        return result


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
        return tk.Spinbox(parent, from_=from_, to=to, width=width,
                          font=self.FONT_MAIN, relief="solid", bd=1,
                          highlightthickness=0, **kw)

    def _entry(self, parent, width=38, **kw):
        return tk.Entry(parent, width=width, font=self.FONT_MAIN,
                        relief="solid", bd=1, highlightthickness=0, **kw)

    def _build_fixed_popup_section(self, parent, trigger, figures, sounds, pack=True):
        """Build one fixed popup LabelFrame into parent. Returns (section_widget, vars_dict)."""
        section = tk.LabelFrame(
            parent,
            text=f"  {TRIGGER_LABELS[trigger]}  ",
            font=self.FONT_TITLE,
            bg=self.PANEL, fg=self.ACCENT,
            relief="groove", bd=1,
            padx=10, pady=8
        )
        if pack:
            section.pack(fill="x", pady=(0, 8), padx=2)

        # Message
        msg_row = tk.Frame(section, bg=self.PANEL)
        msg_row.pack(fill="x", pady=3)
        tk.Label(msg_row, text="Message", font=self.FONT_MAIN,
                 bg=self.PANEL, fg=self.FG, width=14, anchor="w").pack(side="left")
        var_msg = tk.StringVar()
        tk.Entry(msg_row, textvariable=var_msg, width=42,
                 font=self.FONT_MAIN, relief="solid", bd=1,
                 highlightthickness=0).pack(side="left", fill="x", expand=True)

        # Image
        img_row = tk.Frame(section, bg=self.PANEL)
        img_row.pack(fill="x", pady=3)
        tk.Label(img_row, text="Image", font=self.FONT_MAIN,
                 bg=self.PANEL, fg=self.FG, width=14, anchor="w").pack(side="left")
        var_img = tk.StringVar()
        ttk.Combobox(img_row, textvariable=var_img,
                     values=figures, width=20,
                     font=self.FONT_MAIN, state="normal").pack(side="left")

        preview_lbl = tk.Label(img_row, bg=self.PANEL)
        preview_lbl.pack(side="left", padx=(8, 0))

        def _make_preview_updater(lbl, sv):
            def _update(*_):
                path = os.path.join(FIGURES_DIR, sv.get())
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
        ttk.Combobox(snd_row, textvariable=var_snd,
                     values=sounds, width=20,
                     font=self.FONT_MAIN, state="normal").pack(side="left")
        tk.Label(snd_row, text="  Repeat", font=self.FONT_MAIN,
                 bg=self.PANEL, fg=self.FG).pack(side="left")
        var_rep = tk.StringVar()
        tk.Spinbox(snd_row, from_=1, to=10, width=4,
                   textvariable=var_rep,
                   font=self.FONT_MAIN, relief="solid", bd=1,
                   highlightthickness=0).pack(side="left", padx=(4, 0))

        return section, {
            "message":      var_msg,
            "image":        var_img,
            "sound":        var_snd,
            "sound_repeat": var_rep,
        }

    def _build_ui(self):
        figures = list_figures()
        sounds  = list_sounds()

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
        left.pack(side="left", fill="both", expand=False, padx=(0, 8))
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

        self._row(pane2, "Font Name",  self._entry, textvariable=self.var_font,  width=26)
        self._row(pane2, "Text Color", self._entry, textvariable=self.var_color, width=26)
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

        # ── Right panel: single scrollable popup events ───────────────
        right_card, right_pane = self._card(right, title=None)
        right_card.pack(fill="both", expand=True)

        tk.Label(right_pane, text="💬  Popup Events",
                 font=self.FONT_HEAD, bg=self.PANEL, fg=self.FG
                 ).pack(anchor="w", pady=(0, 6))

        canvas = tk.Canvas(right_pane, bg=self.PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_pane, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        scroll_frame = tk.Frame(canvas, bg=self.PANEL)
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.bind("<Enter>",
                    lambda e: canvas.bind_all("<MouseWheel>",
                        lambda ev: canvas.yview_scroll(int(-1*(ev.delta/120)), "units")))
        canvas.bind("<Leave>",
                    lambda e: canvas.unbind_all("<MouseWheel>"))

        # ── Build sections in order: start → work_end → [milestones] → free_end ──
        self._popup_frames = {}

        # start, work_end — packed immediately
        for trigger in FIXED_TRIGGERS_BEFORE:
            section, vars_dict = self._build_fixed_popup_section(
                scroll_frame, trigger, figures, sounds, pack=True
            )
            self._popup_frames[trigger] = vars_dict

        # Divider between milestones and free_end (created but NOT packed yet;
        # BreakMilestoneManager will own its packing order)
        divider = tk.Frame(scroll_frame, height=2, bg=self.BORDER)

        # free_end section — created but NOT packed yet
        free_section, free_vars = self._build_fixed_popup_section(
            scroll_frame, "free_end", figures, sounds, pack=False
        )
        self._popup_frames["free_end"] = free_vars

        # BreakMilestoneManager — takes ownership of divider + free_section packing
        self._milestone_manager = BreakMilestoneManager(
            scroll_frame,
            figures=figures,
            sounds=sounds,
            divider_widget=divider,
            after_widgets=[free_section],
        )

        # Buttons ──────────────────────────────────────────────────────
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
        self._asset_figures_lbl.config(
            text="Images: " + (", ".join(figures) if figures else "none found"))
        self._asset_sounds_lbl.config(
            text="Sounds: " + (", ".join(sounds)  if sounds  else "none found"))

        # Fixed popups
        for trigger, widgets in self._popup_frames.items():
            popup = get_popup(self.cfg, trigger)
            widgets["message"].set(popup.get("message", ""))
            widgets["image"].set(popup.get("image", ""))
            widgets["sound"].set(popup.get("sound", ""))
            widgets["sound_repeat"].set(str(popup.get("sound_repeat", 1)))

        # Break milestones — exact saved order
        milestones = get_break_milestones(self.cfg)
        if not milestones:
            default_break = next(
                (p for p in DEFAULT_CONFIG["popups"] if p["trigger"] == "break_end"),
                None
            )
            if default_break:
                milestones = [default_break]

        self._milestone_manager.load_milestones(milestones)

    def _collect(self):
        try:
            work  = int(self.var_work.get())
            brk   = int(self.var_break.get())
            free  = int(self.var_free.get())
        except ValueError:
            messagebox.showerror("Validation Error",
                                 "Work / Break / Free times must be whole numbers.")
            return None

        popups = []

        for trigger in FIXED_TRIGGERS_BEFORE:
            widgets = self._popup_frames[trigger]
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

        popups.extend(self._milestone_manager.collect_milestones())

        for trigger in FIXED_TRIGGERS_AFTER:
            widgets = self._popup_frames[trigger]
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