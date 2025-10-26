import tkinter as tk
from tkinter import messagebox
import json

THEME_BG = "#f4f6f7"       # light neutral background (medical feel)
THEME_ACCENT = "#0078D7"   # calm blue accent
THEME_TEXT = "#222"        # dark grey text
THEME_FONT = ("Segoe UI", 11)  # clean Windows-style font

# Parameter limits (from PACEMAKER spec and Deliverable 1)
LIMITS = {
    "Lower Rate Limit": (30, 175),
    "Upper Rate Limit": (50, 175),
    "Atrial Amplitude": (0.5, 7.0),
    "Atrial Pulse Width": (0.05, 1.9),
    "Ventricular Amplitude": (0.5, 7.0),
    "Ventricular Pulse Width": (0.05, 1.9),
    "VRP": (150, 500),
    "ARP": (150, 500)
}

MODES = ["AOO", "VOO", "AAI", "VVI"]


class Dashboard:
    def __init__(self, username):
        self.user = username
        self.root = tk.Tk()
        self.root.title(f"DCM – {username}")
        self.root.geometry("550x500")

        tk.Label(self.root, text=f"Welcome {username}", font=("Arial", 14)).pack(pady=10)

        # --- mode selection ---
        self.mode = tk.StringVar(value="AOO")
        frame_modes = tk.LabelFrame(self.root, text="Pacing Mode Selection", bg=THEME_BG, fg=THEME_ACCENT, font=THEME_FONT)
        frame_modes.pack(pady=5)
        for m in MODES:
            tk.Radiobutton(frame_modes, text=m, variable=self.mode,
                           value=m, indicator=0, width=10).pack(side="left", padx=5, pady=5)

        # --- parameter form ---
        self.entries = {}
        frame_params = tk.LabelFrame(self.root, text="Programmable Parameters")
        frame_params.pack(pady=10)
        for i, key in enumerate(LIMITS.keys()):
            tk.Label(frame_params, text=key).grid(row=i, column=0, sticky="e")
            e = tk.Entry(frame_params, width=10)
            e.grid(row=i, column=1)
            self.entries[key] = e

        # --- buttons ---
        tk.Button(self.root, text="Save Parameters",
          bg=THEME_ACCENT, fg="white", font=THEME_FONT, relief="flat",
          command=self.save_params).pack(pady=5)
        tk.Button(self.root, text="Reset", command=self.reset_fields).pack(pady=2)
        tk.Button(self.root, text="About", command=self.about).pack(pady=2)

        self.load_previous()
        self.root.mainloop()

    # ---------- load/save ----------
    def load_previous(self):
        try:
            with open("patients.json") as f:
                data = json.load(f)
        except:
            data = {}
        if self.user in data and self.mode.get() in data[self.user]:
            for k, v in data[self.user][self.mode.get()].items():
                if k in self.entries:
                    self.entries[k].insert(0, v)

    def save_params(self):
        params = {}
        for k, e in self.entries.items():
            try:
                val = float(e.get())
            except:
                messagebox.showerror("Error", f"{k} must be a number.")
                return
            lo, hi = LIMITS[k]
            if not (lo <= val <= hi):
                messagebox.showerror("Error", f"{k} must be {lo}–{hi}.")
                return
            params[k] = val

        try:
            with open("patients.json") as f:
                data = json.load(f)
        except:
            data = {}

        data.setdefault(self.user, {})
        data[self.user][self.mode.get()] = params
        with open("patients.json", "w") as f:
            json.dump(data, f, indent=4)

        messagebox.showinfo("Saved", "Parameters saved successfully.")

    def reset_fields(self):
        for e in self.entries.values():
            e.delete(0, tk.END)

    def about(self):
        messagebox.showinfo("About",
                            "SFWRENG/MECHTRON 3K04 – Deliverable 1\n"
                            "Pacemaker DCM Front-End \n"
                            "Group #: 4")
