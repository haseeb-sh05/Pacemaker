import tkinter as tk
from tkinter import messagebox
import json
import serial, serial.tools.list_ports

# Provides a professional, medical-grade look for the DCM GUI
THEME_BG = "#f4f6f7"       # light neutral background (medical feel)
THEME_ACCENT = "#0078D7"   # calm blue accent for highlights
THEME_TEXT = "#222"        # dark grey text for readability
THEME_FONT = ("Segoe UI", 11)  # clean Windows-style font


# Each programmable pacemaker parameter has a safe operating range
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

# Pacing modes defined in Deliverable 1 specification
MODES = ["AOO", "VOO", "AAI", "VVI"]


def find_ports():
    """Detect available serial (COM) ports on the system."""
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]

# Main user interface window for controlling and monitoring the pacemaker
class Dashboard:
    def __init__(self, username):
        self.user = username          # Current logged-in user
        self.serial = None            # Serial connection object
        self.device_id = None         # Currently connected device's ID

        self.root = tk.Tk()
        self.root.title(f"DCM – {username}")
        self.root.configure(bg=THEME_BG)
        self.root.state("zoomed")  # Opens maximized for clarity

        tk.Label(
            self.root,
            text=f"Welcome {username}",
            bg=THEME_BG,
            fg=THEME_TEXT,
            font=("Segoe UI", 16, "bold")
        ).pack(pady=10)

        # DEVICE CONNECTION
        frame_conn = tk.LabelFrame(
            self.root, text="Device Connection",
            bg=THEME_BG, fg=THEME_ACCENT, font=THEME_FONT
        )
        frame_conn.pack(pady=10)

        # Displays current device connection status (color coded)
        self.device_status = tk.Label(
            frame_conn, text="No device connected",
            bg=THEME_BG, fg="gray", font=THEME_FONT
        )
        self.device_status.pack(pady=5)

        # Find and list available COM ports for user to select
        ports = find_ports()
        if ports:
            # Default to first available COM port
            self.selected_port = tk.StringVar(value=ports[0])
            tk.OptionMenu(frame_conn, self.selected_port, *ports).pack(pady=5)

            # Button to establish serial connection
            tk.Button(
                frame_conn, text="Connect", bg=THEME_ACCENT, fg="white",
                font=THEME_FONT, relief="flat",
                command=lambda: self.connect_device(self.selected_port.get())
            ).pack(pady=5)
        else:
            # Display warning if no COM ports are found
            tk.Label(
                frame_conn, text="No serial ports found",
                bg=THEME_BG, fg="red"
            ).pack(pady=5)

        # PACING MODE SELECTION 
        self.mode = tk.StringVar(value="AOO")  # Default mode

        frame_modes = tk.LabelFrame(
            self.root, text="Pacing Mode Selection",
            bg=THEME_BG, fg=THEME_ACCENT, font=THEME_FONT
        )
        frame_modes.pack(pady=5)

        # Creates four radio buttons (AOO, VOO, AAI, VVI)
        for m in MODES:
            tk.Radiobutton(
                frame_modes, text=m, variable=self.mode,
                value=m, indicator=0, width=10,
                bg=THEME_BG, fg=THEME_TEXT, font=THEME_FONT,
                selectcolor=THEME_ACCENT
            ).pack(side="left", padx=5, pady=5)

        # PARAMETER ENTRY FORM
        self.entries = {}
        frame_params = tk.LabelFrame(
            self.root, text="Programmable Parameters",
            bg=THEME_BG, fg=THEME_ACCENT, font=THEME_FONT
        )
        frame_params.pack(pady=10)

        # Generate entry fields dynamically from LIMITS dictionary
        for i, key in enumerate(LIMITS.keys()):
            tk.Label(
                frame_params, text=key,
                bg=THEME_BG, fg=THEME_TEXT, font=THEME_FONT
            ).grid(row=i, column=0, sticky="e", padx=5, pady=3)

            e = tk.Entry(frame_params, width=10, font=THEME_FONT)
            e.grid(row=i, column=1, padx=5, pady=3)
            self.entries[key] = e

        # SECTION 4: CONTROL BUTTONS
        tk.Button(
            self.root, text="Save Parameters",
            bg=THEME_ACCENT, fg="white", font=THEME_FONT, relief="flat",
            command=self.save_params
        ).pack(pady=5)

        tk.Button(self.root, text="Reset", command=self.reset_fields).pack(pady=2)
        tk.Button(self.root, text="About", command=self.about).pack(pady=2)

        # Load any previously saved parameters for this user
        self.load_previous()

        # Run the main UI event loop
        self.root.mainloop()

    # SERIAL DEVICE CONNECTION HANDLER
    def connect_device(self, port):
        """Connect to the pacemaker hardware and retrieve its unique ID."""
        try:
            # Open the selected COM port at 115200 baud
            self.serial = serial.Serial(port, 115200, timeout=2)
            self.serial.reset_input_buffer()

            # Request device ID (microcontroller should respond with DEVICE_ID:<id>)
            self.serial.write(b"ID?\n")
            line = self.serial.readline().decode(errors="ignore").strip()

            if line.startswith("DEVICE_ID:"):
                self.device_id = line.split(":")[1]  # Extract the ID string
            else:
                # If no response, assign a simulated ID
                self.device_id = f"SIM-{port}"

            # Compare this device ID with previously stored one
            self.check_device_id()

        except Exception as e:
            # If unable to connect, show an error
            messagebox.showerror("Connection Error", f"Could not connect to {port}\n\n{e}")
            self.device_status.config(text="Connection failed", fg="red")

    def check_device_id(self):
        """Compare connected device ID with the previously used one."""
        try:
            with open("device_id.json") as f:
                data = json.load(f)
        except:
            data = {}

        # Retrieve last known device ID from file
        last_id = data.get("last_device", None)

        # Determine connection status based on comparison
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

        # Update stored device ID
        with open("device_id.json", "w") as f:
            json.dump(data, f, indent=4)

        # Display connection status and ID in the GUI
        self.device_status.config(text=f"{status}\nID: {self.device_id}", fg=color)

    # LOAD / SAVE USER PARAMETERS
    def load_previous(self):
        """Load previously saved pacing parameters for this user."""
        try:
            with open("patients.json") as f:
                data = json.load(f)
        except:
            data = {}

        # Load values for current mode if they exist
        if self.user in data and self.mode.get() in data[self.user]:
            for k, v in data[self.user][self.mode.get()].items():
                if k in self.entries:
                    self.entries[k].insert(0, v)

    def save_params(self):
        """Validate and save the entered parameters to patients.json."""
        params = {}

        # Validate each entry against numeric and range limits
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

        # Load previous patient data if it exists
        try:
            with open("patients.json") as f:
                data = json.load(f)
        except:
            data = {}

        # Save new or updated data for this user and mode
        data.setdefault(self.user, {})
        data[self.user][self.mode.get()] = params

        # Write changes to disk
        with open("patients.json", "w") as f:
            json.dump(data, f, indent=4)

        messagebox.showinfo("Saved", "Parameters saved successfully.")

    # RESET & ABOUT BUTTONS
    def reset_fields(self):
        """Clear all parameter entry fields."""
        for e in self.entries.values():
            e.delete(0, tk.END)

    def about(self):
        """Display course and project information."""
        messagebox.showinfo(
            "About",
            "SFWRENG/MECHTRON 3K04 – Deliverable 1\n"
            "Pacemaker DCM Front-End\n"
            "Includes Serial Device ID Detection\n"
            "Group #: 4"
        )
