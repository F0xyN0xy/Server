import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import requests
import json

API_BASE_URL = "http://localhost:5000/api"

# ------------------- API Helper Functions -------------------
def api_request(method, endpoint, data=None):
    """Make API request and return response"""
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url, json=data)
        
        return response.json(), response.status_code
    except requests.exceptions.ConnectionError:
        messagebox.showerror("Connection Error", "Could not connect to server. Make sure the Flask server is running.")
        return None, None
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        return None, None

# ------------------- Registration -------------------
def open_register_window():
    reg = tk.Toplevel(root)
    reg.title("Create Account")
    reg.geometry("400x500")
    reg.configure(bg="#1e1e1e")

    tk.Label(reg, text="Register", fg="white", bg="#1e1e1e", font=("Arial", 16)).pack(pady=5)

    tk.Label(reg, text="Email *", fg="white", bg="#1e1e1e").pack()
    entry_email = tk.Entry(reg, width=30)
    entry_email.pack()

    tk.Label(reg, text="Password *", fg="white", bg="#1e1e1e").pack()
    entry_pw1 = tk.Entry(reg, width=30, show="*")
    entry_pw1.pack()

    tk.Label(reg, text="Repeat password *", fg="white", bg="#1e1e1e").pack()
    entry_pw2 = tk.Entry(reg, width=30, show="*")
    entry_pw2.pack()

    tk.Label(reg, text="Name", fg="white", bg="#1e1e1e").pack()
    entry_name = tk.Entry(reg, width=30)
    entry_name.pack()

    tk.Label(reg, text="Last name", fg="white", bg="#1e1e1e").pack()
    entry_lastname = tk.Entry(reg, width=30)
    entry_lastname.pack()

    tk.Label(reg, text="Phone", fg="white", bg="#1e1e1e").pack()
    entry_tel = tk.Entry(reg, width=30)
    entry_tel.pack()

    strength_label = tk.Label(reg, text="Password strength: -", fg="white", bg="#1e1e1e")
    strength_label.pack(pady=5)

    def update_strength(event):
        pw = entry_pw1.get()
        if pw:
            result, status = api_request("POST", "password-strength", {"password": pw})
            if result:
                strength = result.get("strength", "")
                if strength == "weak":
                    strength_label.config(text="Password strength: weak", fg="red")
                elif strength == "medium":
                    strength_label.config(text="Password strength: medium", fg="orange")
                else:
                    strength_label.config(text="Password strength: strong", fg="lightgreen")
    
    entry_pw1.bind("<KeyRelease>", update_strength)

    def register():
        email = entry_email.get().strip()
        pw1 = entry_pw1.get()
        pw2 = entry_pw2.get()
        name = entry_name.get()
        lastname = entry_lastname.get()
        tel = entry_tel.get()

        if not email or not pw1 or not pw2:
            messagebox.showerror("Error", "Email and password are required fields.")
            return

        if pw1 != pw2:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        data = {
            "email": email,
            "password": pw1,
            "name": name,
            "lastname": lastname,
            "telephone": tel
        }

        result, status = api_request("POST", "register", data)
        if result and result.get("success"):
            messagebox.showinfo("Success", result.get("message"))
            reg.destroy()
        elif result:
            messagebox.showerror("Error", result.get("message"))

    tk.Button(reg, text="Register", command=register).pack(pady=10)

# ------------------- Login -------------------
def login():
    email = entry_login_email.get().strip()
    pw = entry_login_pw.get()

    data = {
        "email": email,
        "password": pw
    }

    result, status = api_request("POST", "login", data)
    if result and result.get("success"):
        messagebox.showinfo("Success", "Login successful!")
        open_profile(email)
    elif result:
        messagebox.showerror("Error", result.get("message"))

# ----------------- Forgot Password -----------------
def forgot_password_window():
    win = tk.Toplevel(root)
    win.title("Forgot Password")
    win.geometry("330x180")
    win.configure(bg="#1e1e1e")

    tk.Label(win, text="Your Email:", fg="white", bg="#1e1e1e").pack(pady=10)
    email_entry = tk.Entry(win, width=30)
    email_entry.pack()

    def send_reset():
        email = email_entry.get().strip()
        
        result, status = api_request("POST", "forgot-password", {"email": email})
        if result and result.get("success"):
            messagebox.showinfo("Success", result.get("message"))
            win.destroy()
            open_reset_window(email)
        elif result:
            messagebox.showerror("Error", result.get("message"))

    tk.Button(win, text="Send Reset Code", command=send_reset).pack(pady=15)

def open_reset_window(email):
    win = tk.Toplevel(root)
    win.title("Set New Password")
    win.geometry("400x300")
    win.configure(bg="#1e1e1e")

    tk.Label(win, text="Reset-Code:", fg="white", bg="#1e1e1e").pack(pady=5)
    entry_code = tk.Entry(win, width=30)
    entry_code.pack()

    tk.Label(win, text="New Password:", fg="white", bg="#1e1e1e").pack()
    entry_pw1 = tk.Entry(win, width=30, show="*")
    entry_pw1.pack()

    tk.Label(win, text="Repeat Password:", fg="white", bg="#1e1e1e").pack()
    entry_pw2 = tk.Entry(win, width=30, show="*")
    entry_pw2.pack()

    def reset_pw():
        code = entry_code.get().strip()
        pw1 = entry_pw1.get()
        pw2 = entry_pw2.get()

        if pw1 != pw2:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        data = {
            "email": email,
            "code": code,
            "password": pw1
        }

        result, status = api_request("POST", "reset-password", data)
        if result and result.get("success"):
            messagebox.showinfo("Success", result.get("message"))
            win.destroy()
        elif result:
            messagebox.showerror("Error", result.get("message"))

    tk.Button(win, text="Change Password", command=reset_pw).pack(pady=15)

# --------------- Open Profile Window ---------------
def open_profile(email):
    # Fetch current profile data
    result, status = api_request("GET", f"profile/{email}")
    if not result or not result.get("success"):
        messagebox.showerror("Error", "Could not load profile")
        return

    user_data = result["user"]["data"]

    profile = tk.Toplevel(root)
    profile.title(f"Profile - {email}")
    profile.geometry("400x350")
    profile.configure(bg="#1e1e1e")

    tk.Label(profile, text="Profile", fg="white", bg="#1e1e1e", font=("Arial",16)).pack(pady=10)

    # Variables for editing
    name_var = tk.StringVar(value=user_data.get("name",""))
    lastname_var = tk.StringVar(value=user_data.get("lastname",""))
    tel_var = tk.StringVar(value=user_data.get("telephone",""))
    email_var = tk.StringVar(value=email)

    def label_entry(text, var):
        tk.Label(profile, text=text, fg="white", bg="#1e1e1e", anchor="w").pack(fill="x", padx=20)
        tk.Entry(profile, textvariable=var, width=30).pack(padx=20, pady=3, fill="x")

    label_entry("Name:", name_var)
    label_entry("Last name:", lastname_var)
    label_entry("Telephone:", tel_var)
    label_entry("E-Mail:", email_var)

    # Save function
    def save_changes():
        data = {
            "email": email_var.get().strip(),
            "name": name_var.get(),
            "lastname": lastname_var.get(),
            "telephone": tel_var.get()
        }

        result, status = api_request("PUT", f"profile/{email}", data)
        if result and result.get("success"):
            messagebox.showinfo("Success", result.get("message"))
            profile.destroy()
        elif result:
            messagebox.showerror("Error", result.get("message"))

    # Delete account
    def delete_account():
        pw = tk.simpledialog.askstring("Confirm password", "Enter your password:", show="*") # type: ignore
        if pw is None:
            return

        if messagebox.askyesno("Delete account", "Do you really want to delete your account?"):
            result, status = api_request("DELETE", f"profile/{email}", {"password": pw})
            if result and result.get("success"):
                messagebox.showinfo("Success", result.get("message"))
                profile.destroy()
            elif result:
                messagebox.showerror("Error", result.get("message"))

    tk.Button(profile, text="Save", command=save_changes, width=15).pack(pady=10)
    tk.Button(profile, text="Delete account", command=delete_account, width=15, bg="red", fg="white").pack(pady=5)

# ------------------- Main window -------------------
root = tk.Tk()
root.title("Login")
root.geometry("500x450")
root.configure(bg="#1e1e1e")

tk.Label(root, text="Login", fg="white", bg="#1e1e1e", font=("Arial", 16)).pack(pady=10)

tk.Label(root, text="E-Mail:", fg="white", bg="#1e1e1e").pack()
entry_login_email = tk.Entry(root, width=30)
entry_login_email.pack()

tk.Label(root, text="Password:", fg="white", bg="#1e1e1e").pack()
entry_login_pw = tk.Entry(root, width=30, show="*")
entry_login_pw.pack()

tk.Button(root, text="Login", command=login).pack(pady=10)
tk.Button(root, text="Forgot Password", command=forgot_password_window).pack(pady=5)
tk.Button(root, text="Create Account", command=open_register_window).pack()

root.mainloop()