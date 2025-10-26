import tkinter as tk
from tkinter import messagebox
import json, hashlib
from ui_dashboard import Dashboard

THEME_BG = "#f4f6f7"       # light neutral background (medical feel)
THEME_ACCENT = "#0078D7"   # calm blue accent
THEME_TEXT = "#222"        # dark grey text
THEME_FONT = ("Segoe UI", 11)  # clean Windows-style font


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DCM Login")
        self.root.configure(bg=THEME_BG)
        self.root.geometry("400x280")
        self.root.eval('tk::PlaceWindow . center')

        # Header label
        tk.Label(
            self.root,
            text="Device Controller–Monitor",
            bg=THEME_BG,
            fg=THEME_ACCENT,
            font=("Segoe UI", 16, "bold")
        ).pack(pady=20)

        # Styled buttons
        for text, cmd in [("Login", self.login_screen),
                        ("Register", self.register_screen),
                        ("Quit", self.root.destroy)]:
            tk.Button(
                self.root,
                text=text,
                width=15,
                command=cmd,
                bg=THEME_ACCENT,
                fg="white",
                font=THEME_FONT,
                relief="flat",
                activebackground="#005A9E"
            ).pack(pady=7)

        self.root.mainloop()

    # ----- helpers -----
    def load_users(self):
        try:
            with open("users.json") as f:
                return json.load(f)
        except:
            return []

    def save_users(self, users):
        with open("users.json", "w") as f:
            json.dump(users, f, indent=4)

    # ----- register -----
    def register_screen(self):
        win = tk.Toplevel(self.root)
        win.title("Register")
        win.configure(bg=THEME_BG)
        win.geometry("360x190")
        
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (w // 2)
        y = (win.winfo_screenheight() // 2) - (h // 2)
        win.geometry(f"+{x}+{y}")


        frame = tk.Frame(win, bg=THEME_BG, padx=20, pady=20)
        frame.pack()

        tk.Label(frame, text="Username", bg=THEME_BG, fg=THEME_TEXT, font=THEME_FONT).grid(row=0, column=0, pady=5, sticky="e")
        tk.Label(frame, text="Password", bg=THEME_BG, fg=THEME_TEXT, font=THEME_FONT).grid(row=1, column=0, pady=5, sticky="e")

        u = tk.Entry(frame, width=20)
        p = tk.Entry(frame, show="*", width=20)
        u.grid(row=0, column=1, pady=5)
        p.grid(row=1, column=1, pady=5)


        def register():
            username = u.get().strip()
            password = p.get().strip()

            # --- Input validation ---
            if username == "" or password == "":
                messagebox.showerror("Error", "Username and password cannot be empty.")
                return
            if len(password) < 4:
                messagebox.showerror("Error", "Password must be at least 4 characters long.")
                return
        
            users = self.load_users()
            if len(users) >= 10:
                messagebox.showerror("Limit Reached", "Maximum of 10 users allowed.")
                return
            if any(x["user"] == u.get() for x in users):
                messagebox.showerror("Error", "User already exists.")
                return
            users.append({"user": u.get(), "pw": hash_pw(p.get())})
            self.save_users(users)
            messagebox.showinfo("Registered", "User registered successfully.")
            win.destroy()

        
        tk.Button(frame, text="Register",
                bg=THEME_ACCENT, fg="white", font=THEME_FONT,
                relief="flat", command=register).grid(row=2, column=0, columnspan=2, pady=10)

    # ----- login -----
    def login_screen(self):
        win = tk.Toplevel(self.root)
        win.title("Login")
        win.configure(bg=THEME_BG)
        win.geometry("360x190")

        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (w // 2)
        y = (win.winfo_screenheight() // 2) - (h // 2)
        win.geometry(f"+{x}+{y}")


        frame = tk.Frame(win, bg=THEME_BG, padx=15, pady=15)
        frame.pack()

        tk.Label(frame, text="Username", bg=THEME_BG, fg=THEME_TEXT, font=THEME_FONT).grid(row=0, column=0, pady=5, sticky="e")
        tk.Label(frame, text="Password", bg=THEME_BG, fg=THEME_TEXT, font=THEME_FONT).grid(row=1, column=0, pady=5, sticky="e")

        u = tk.Entry(frame, width=20)
        p = tk.Entry(frame, show="*", width=20)
        u.grid(row=0, column=1, pady=5)
        p.grid(row=1, column=1, pady=5)


        def login():
            users = self.load_users()
            for x in users:
                if x["user"] == u.get() and x["pw"] == hash_pw(p.get()):
                    messagebox.showinfo("Login", f"Welcome {x['user']}")
                    self.root.destroy()
                    Dashboard(x["user"])
                    return
            messagebox.showerror("Error", "Invalid credentials.")

        tk.Button(frame, text="Login",
        bg=THEME_ACCENT, fg="white", font=THEME_FONT,
        relief="flat", command=login).grid(row=2, column=0, columnspan=2, pady=10)