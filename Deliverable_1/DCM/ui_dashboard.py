import tkinter as tk
from tkinter import messagebox
import json
import serial, serial.tools.list_ports

# THEME SETTINGS 
THEME_BG = "#f4f6f7"       # light neutral background (medical feel)
THEME_ACCENT = "#0078D7"   # calm blue accent
THEME_TEXT = "#222"        # dark grey text
THEME_FONT = ("Segoe UI", 11)  # clean Windows-style font

# PARAMETER LIMITS 
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

# HELPER: PORT DETECTION 
def find_ports():
    """Detect available COM ports."""
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]

# MAIN DASHBOARD CLASS 
class Dashboard:
    def __init__(self, username):
        self.user = username
        self.serial = None
        self.device_id = None

        self.root = tk.Tk()
        self.root.title(f"DCM – {username}")
        self.root.configure(bg=THEME_BG)
        self.root.state("zoomed")  # open maximized

        tk.Label(
            self.root,
            text=f"Welcome {username}",
            bg=THEME_BG,
            fg=THEME_TEXT,
            font=("Segoe UI", 16, "bold")
        ).pack(pady=10)

        # DEVICE CONNECTION SECTION 
        frame_conn = tk.LabelFrame(
            self.root, text="Device Connection",
            bg=THEME_BG, fg=THEME_ACCENT, font=THEME_FONT
        )
        frame_conn.pack(pady=10)

        self.device_status = tk.Label(
            frame_conn, text="No device connected",
            bg=THEME_BG, fg="gray", font=THEME_FONT
        )
        self.device_status.pack(pady=5)

        ports = find_ports()
        if ports:
            self.selected_port = tk.StringVar(value=ports[0])
            tk.OptionMenu(frame_conn, self.selected_port, *ports).pack(pady=5)
            tk.Button(
                frame_conn, text="Connect", bg=THEME_ACCENT, fg="white",
                font=THEME_FONT, relief="flat",
                command=lambda: self.connect_device(self.selected_port.get())
            ).pack(pady=5)
        else:
            tk.Label(
                frame_conn, text="No serial ports found",
                bg=THEME_BG, fg="red"
            ).pack(pady=5)

        # MODE SELECTION SECTION 
        self.mode = tk.StringVar(value="AOO")
        frame_modes = tk.LabelFrame(
            self.root, text="Pacing Mode Selection",
            bg=THEME_BG, fg=THEME_ACCENT, font=THEME_FONT
        )
        frame_modes.pack(pady=5)
        for m in MODES:
            tk.Radiobutton(
                frame_modes, text=m, variable=self.mode,
                value=m, indicator=0, width=10,
                bg=THEME_BG, fg=THEME_TEXT, font=THEME_FONT,
                selectcolor=THEME_ACCENT
            ).pack(side="left", padx=5, pady=5)

        # PARAMETER ENTRY SECTION 
        self.entries = {}
        frame_params = tk.LabelFrame(
            self.root, text="Programmable Parameters",
            bg=THEME_BG, fg=THEME_ACCENT, font=THEME_FONT
        )
        frame_params.pack(pady=10)
        for i, key in enumerate(LIMITS.keys()):
            tk.Label(
                frame_params, text=key,
                bg=THEME_BG, fg=THEME_TEXT, font=THEME_FONT
            ).grid(row=i, column=0, sticky="e", padx=5, pady=3)
            e = tk.Entry(frame_params, width=10, font=THEME_FONT)
            e.grid(row=i, column=1, padx=5, pady=3)
            self.entries[key] = e

        # CONTROL BUTTONS 
        tk.Button(
            self.root, text="Save Parameters",
            bg=THEME_ACCENT, fg="white", font=THEME_FONT, relief="flat",
            command=self.save_params
        ).pack(pady=5)

        tk.Button(
            self.root, text="Reset",
            bg=THEME_ACCENT, fg="white", font=THEME_FONT, relief="flat",
            command=self.reset_fields
        ).pack(pady=2)

        tk.Button(
            self.root, text="About",
            bg=THEME_ACCENT, fg="white", font=THEME_FONT, relief="flat",
            command=self.about
        ).pack(pady=2)

        self.load_previous()
        self.root.mainloop()

    # SERIAL CONNECTION 
    def connect_device(self, port):
        """Connect to the pacemaker hardware and read its device ID."""
        try:
            self.serial = serial.Serial(port, 115200, timeout=2)
            self.serial.reset_input_buffer()

            # Try requesting ID from hardware
            self.serial.write(b"ID?\n")
            line = self.serial.readline().decode(errors="ignore").strip()

            if line.startswith("DEVICE_ID:"):
                self.device_id = line.split(":")[1]
            else:
                # fallback if hardware doesn’t reply
                self.device_id = f"SIM-{port}"

            self.check_device_id()

        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to {port}\n\n{e}")
            self.device_status.config(text="Connection failed", fg="red")

    def check_device_id(self):
        """Compare connected device ID with previously stored one."""
        try:
            with open("device_id.json") as f:
                data = json.load(f)
        except:
            data = {}

        last_id = data.get("last_device", None)

        if last_id is None:
            status = "🟢 New device connected"
            data["last_device"] = self.device_id
            color = "green"
        elif self.device_id == last_id:
            status = "✅ Same device connected"
            color = "green"
        else:
            status = "⚠️ Different device detected"
            data["last_device"] = self.device_id
            color = "red"

        with open("device_id.json", "w") as f:
            json.dump(data, f, indent=4)

        # Update UI
        self.device_status.config(text=f"{status}\nID: {self.device_id}", fg=color)

    # PARAMETER LOADING / SAVING 
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
            val_str = e.get().strip()
            if val_str == "":
                messagebox.showerror("Error", f"{k} cannot be empty.")
                return
            try:
                val = float(val_str)
            except:
                messagebox.showerror("Error", f"{k} must be a number.")
                return
            lo, hi = LIMITS[k]
            if not (lo <= val <= hi):
                messagebox.showerror("Error", f"{k} must be between {lo}–{hi}.")
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

    # RESET FIELDS 
    def reset_fields(self):
        for e in self.entries.values():
            e.delete(0, tk.END)

    # ABOUT 
    def about(self):
        messagebox.showinfo(
            "About",
            "SFWRENG/MECHTRON 3K04 – Deliverable 1\n"
            "Pacemaker DCM Front-End\n"
            "Includes Serial Device ID Detection\n"
            "Group #: 4"
        )
