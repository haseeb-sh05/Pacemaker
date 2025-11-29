import tkinter as tk
from tkinter import messagebox
import json
import serial, serial.tools.list_ports

# Theme colors and font used throughout the interface
THEME_BG = "#f4f6f7"
THEME_ACCENT = "#0078D7"
THEME_TEXT = "#222"
THEME_FONT = ("Segoe UI", 11)

# Parameter ranges based on the project specification
LIMITS = {
    "Lower Rate Limit": (30, 175),
    "Upper Rate Limit": (50, 175),
    "Maximum Sensor Rate": (50, 175),

    "ARP": (150, 500),
    "VRP": (150, 500),
    "PVARP": (150, 500),

    "Atrial Amplitude": (0, 7),
    "Ventricular Amplitude": (0, 7),

    "Atrial Pulse Width": (0, 50),
    "Ventricular Pulse Width": (0, 50),

    "Atrial Sensitivity": (0, 10),
    "Ventricular Sensitivity": (0, 10),

    "Reaction Time": (0, 10),
    "Recovery Time": (0, 10),

    "Response Factor": (0, 10),
    "Activity Threshold": (0, 10)
}

# List of supported pacing modes
MODES = ["AOO", "VOO", "AAI", "VVI", "AOOR", "VOOR", "AAIR", "VVIR"]

# Mapping each mode to the byte value expected by the pacemaker
MODE_MAP = {
    "AOO": 0, "VOO": 1, "AAI": 2, "VVI": 3,
    "AOOR": 4, "VOOR": 5, "AAIR": 6, "VVIR": 7
}

# Safely convert text input into an integer
def safe_int(v):
    v = v.strip()
    if v == "":
        return 0
    try:
        return int(float(v))
    except:
        return 0

# Detect available serial ports on the system
def find_ports():
    return [p.device for p in serial.tools.list_ports.comports()]

class Dashboard:
    def __init__(self, username):
        self.user = username
        self.serial = None
        self.device_id = None

        # Main window setup
        self.root = tk.Tk()
        self.root.state("zoomed")
        self.root.title(f"DCM – {username}")
        self.root.configure(bg=THEME_BG)

        tk.Label(self.root, text=f"Welcome {username}",
                 bg=THEME_BG, fg=THEME_TEXT,
                 font=("Segoe UI", 18, "bold")).pack(pady=10)

        # Device connection area
        frame_conn = tk.LabelFrame(self.root, text="Device Connection",
                                   bg=THEME_BG, fg=THEME_ACCENT,
                                   font=THEME_FONT)
        frame_conn.pack(pady=10)

        self.device_status = tk.Label(frame_conn, text="No device connected",
                                      bg=THEME_BG, fg="gray", font=THEME_FONT)
        self.device_status.pack(pady=5)

        ports = find_ports()
        if ports:
            self.selected_port = tk.StringVar(value=ports[0])
            tk.OptionMenu(frame_conn, self.selected_port, *ports).pack(pady=5)
            tk.Button(frame_conn, text="Connect",
                      bg=THEME_ACCENT, fg="white", font=THEME_FONT,
                      command=lambda: self.connect_device(self.selected_port.get())
                      ).pack(pady=5)
        else:
            tk.Label(frame_conn, text="No COM ports found",
                     bg=THEME_BG, fg="red").pack(pady=5)

        # Pacing mode selection
        self.mode = tk.StringVar(value="AOO")
        frame_modes = tk.LabelFrame(self.root, text="Pacing Mode Selection",
                                    bg=THEME_BG, fg=THEME_ACCENT, font=THEME_FONT)
        frame_modes.pack(pady=5)

        for m in MODES:
            tk.Radiobutton(frame_modes, text=m, variable=self.mode, value=m,
                           indicator=0, width=8, bg=THEME_BG, fg=THEME_TEXT,
                           font=THEME_FONT, selectcolor=THEME_ACCENT).pack(side="left", padx=5)

        # Parameter entry area (two columns)
        frame_params = tk.LabelFrame(self.root, text="Programmable Parameters",
                                     bg=THEME_BG, fg=THEME_ACCENT, font=THEME_FONT)
        frame_params.pack(pady=10)

        self.entries = {}
        self.sliders = {}

        all_params = list(LIMITS.keys())
        left = all_params[:8]
        right = all_params[8:]

        # Left column parameters
        for i, key in enumerate(left):
            lo, hi = LIMITS[key]

            tk.Label(frame_params, text=key, bg=THEME_BG, fg=THEME_TEXT,
                     font=THEME_FONT).grid(row=i, column=0, sticky="e", padx=5, pady=4)

            entry = tk.Entry(frame_params, width=8, font=THEME_FONT)
            entry.grid(row=i, column=1, padx=5)
            self.entries[key] = entry

            slider = tk.Scale(frame_params, from_=lo, to=hi, orient="horizontal",
                              length=180, resolution=1, bg=THEME_BG,
                              fg=THEME_TEXT, highlightthickness=0,
                              command=lambda v, k=key: self.update_entry_from_slider(k, v))
            slider.grid(row=i, column=2, padx=5)
            self.sliders[key] = slider

            entry.bind("<KeyRelease>", lambda e, k=key: self.update_slider_from_entry(k))

        # Right column parameters
        for i, key in enumerate(right):
            lo, hi = LIMITS[key]

            tk.Label(frame_params, text=key, bg=THEME_BG, fg=THEME_TEXT,
                     font=THEME_FONT).grid(row=i, column=3, sticky="e", padx=25, pady=4)

            entry = tk.Entry(frame_params, width=8, font=THEME_FONT)
            entry.grid(row=i, column=4, padx=5)
            self.entries[key] = entry

            slider = tk.Scale(frame_params, from_=lo, to=hi, orient="horizontal",
                              length=180, resolution=1, bg=THEME_BG,
                              fg=THEME_TEXT, highlightthickness=0,
                              command=lambda v, k=key: self.update_entry_from_slider(k, v))
            slider.grid(row=i, column=5, padx=5)
            self.sliders[key] = slider

            entry.bind("<KeyRelease>", lambda e, k=key: self.update_slider_from_entry(k))

        # Egram enable flag
        self.egram_flag = tk.IntVar()
        tk.Checkbutton(self.root, text="Enable EGRAM (1 = YES)",
                       variable=self.egram_flag,
                       bg=THEME_BG, fg=THEME_TEXT,
                       font=THEME_FONT).pack(pady=10)

        # Action buttons
        tk.Button(self.root, text="Save Parameters",
                  bg=THEME_ACCENT, fg="white",
                  font=THEME_FONT,
                  command=self.save_params).pack(pady=5)

        tk.Button(self.root, text="Reset", command=self.reset_fields).pack(pady=2)
        tk.Button(self.root, text="About", command=self.about).pack(pady=2)

        self.load_previous()
        self.root.mainloop()

    def connect_device(self, port):
        try:
            self.serial = serial.Serial(port, 115200, timeout=1)
            self.serial.reset_input_buffer()

            self.serial.write(b"ID?\n")
            rx = self.serial.readline().decode().strip()

            if rx.startswith("DEVICE_ID"):
                self.device_id = rx.split(":")[1]
            else:
                self.device_id = "UNKNOWN"

            self.device_status.config(
                text=f"Connected\nID: {self.device_id}", fg="green"
            )

            packet = self.build_packet()
            if packet:
                self.serial.write(packet)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect:\n{e}")

    # Validates numerical limits + ensures LRL ≤ URL
    def validate_parameters(self):
        values = {}

        for key, entry in self.entries.items():
            val_str = entry.get().strip()
            if val_str == "":
                messagebox.showerror("Error", f"{key} cannot be empty.")
                return False

            try:
                val = float(val_str)
            except:
                messagebox.showerror("Error", f"{key} must be a number.")
                return False

            lo, hi = LIMITS[key]
            if not (lo <= val <= hi):
                messagebox.showerror("Error", f"{key} must be between {lo} and {hi}.")
                return False

            values[key] = val

        if values["Lower Rate Limit"] > values["Upper Rate Limit"]:
            messagebox.showerror("Error",
                                 "Lower Rate Limit must be ≤ Upper Rate Limit.")
            return False

        return True

    # Creates the exact 20-byte packet required for hardware/Simulink
    def build_packet(self):
        try:
            packet = bytearray()
            packet.append(0x16)
            packet.append(0x55)
            packet.append(MODE_MAP[self.mode.get()])

            order = [
                "Lower Rate Limit",
                "Upper Rate Limit",
                "Maximum Sensor Rate",

                "ARP",
                "VRP",
                "PVARP",

                "Atrial Amplitude",
                "Ventricular Amplitude",

                "Atrial Pulse Width",
                "Ventricular Pulse Width",

                "Atrial Sensitivity",
                "Ventricular Sensitivity",

                "Reaction Time",
                "Recovery Time",

                "Response Factor",
                "Activity Threshold"
            ]

            for key in order:
                packet.append(safe_int(self.entries[key].get()))

            packet.append(self.egram_flag.get())

            print("PACKET =", list(packet))
            print("PACKET LENGTH =", len(packet))
            return packet

        except Exception as e:
            messagebox.showerror("Error", f"Packet build failed:\n{e}")
            return None

    def save_params(self):
        if not self.validate_parameters():
            return

        params = {k: safe_int(e.get()) for k, e in self.entries.items()}

        try:
            with open("patients.json") as f:
                data = json.load(f)
        except:
            data = {}

        if self.user not in data:
            data[self.user] = {}

        data[self.user][self.mode.get()] = params

        with open("patients.json", "w") as f:
            json.dump(data, f, indent=4)

        messagebox.showinfo("Saved", "Parameters saved!")

    def update_entry_from_slider(self, key, value):
        self.entries[key].delete(0, tk.END)
        self.entries[key].insert(0, str(value))

    def update_slider_from_entry(self, key):
        try:
            val = safe_int(self.entries[key].get())
            lo, hi = LIMITS[key]
            if lo <= val <= hi:
                self.sliders[key].set(val)
        except:
            pass

    def reset_fields(self):
        for e in self.entries.values():
            e.delete(0, tk.END)

    def about(self):
        messagebox.showinfo(
            "About",
            "SFWRENG 3K04 – Deliverable 2\nPacemaker DCM Front-End\nGroup 4"
        )

    def load_previous(self):
        try:
            with open("patients.json") as f:
                data = json.load(f)
        except:
            return

        if self.user in data and self.mode.get() in data[self.user]:
            for k, v in data[self.user][self.mode.get()].items():
                if k in self.entries:
                    self.entries[k].insert(0, str(v))
                    try:
                        self.sliders[k].set(int(v))
                    except:
                        pass


if __name__ == "__main__":
    Dashboard("TestUser")
