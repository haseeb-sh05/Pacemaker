import tkinter as tk
from tkinter import messagebox
import json, hashlib
from ui_dashboard import Dashboard


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DCM Login")
        self.root.geometry("400x260")
        tk.Label(self.root, text="Device Controller–Monitor", font=("Arial", 16, "bold")).pack(pady=20)

        tk.Button(self.root, text="Login", width=15, command=self.login_screen).pack(pady=5)
        tk.Button(self.root, text="Register", width=15, command=self.register_screen).pack(pady=5)
        tk.Button(self.root, text="Quit", width=15, command=self.root.destroy).pack(pady=5)

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

        tk.Label(win, text="Username").grid(row=0, column=0)
        tk.Label(win, text="Password").grid(row=1, column=0)
        u = tk.Entry(win)
        p = tk.Entry(win, show="*")
        u.grid(row=0, column=1)
        p.grid(row=1, column=1)

        def register():
            users = self.load_users()
            if len(users) >= 10:
                messagebox.showerror("Limit", "Maximum 10 users allowed.")
                return
            if any(x["user"] == u.get() for x in users):
                messagebox.showerror("Error", "User already exists.")
                return
            users.append({"user": u.get(), "pw": hash_pw(p.get())})
            self.save_users(users)
            messagebox.showinfo("Registered", "User registered successfully.")
            win.destroy()

        tk.Button(win, text="Register", command=register).grid(row=2, column=0, columnspan=2, pady=5)

    # ----- login -----
    def login_screen(self):
        win = tk.Toplevel(self.root)
        win.title("Login")

        tk.Label(win, text="Username").grid(row=0, column=0)
        tk.Label(win, text="Password").grid(row=1, column=0)
        u = tk.Entry(win)
        p = tk.Entry(win, show="*")
        u.grid(row=0, column=1)
        p.grid(row=1, column=1)

        def login():
            users = self.load_users()
            for x in users:
                if x["user"] == u.get() and x["pw"] == hash_pw(p.get()):
                    messagebox.showinfo("Login", f"Welcome {x['user']}")
                    self.root.destroy()
                    Dashboard(x["user"])
                    return
            messagebox.showerror("Error", "Invalid credentials.")

        tk.Button(win, text="Login", command=login).grid(row=2, column=0, columnspan=2, pady=5)