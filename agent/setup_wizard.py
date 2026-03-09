"""
setup_wizard.py — First-Run Setup Wizard
Laptop Life-Saver System | Nyanza District

A lightweight GUI to collect user info and establish privacy trust.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from PIL import Image, ImageTk

class SetupWizard:
    def __init__(self, logo_path, config_path):
        self.root = tk.Tk()
        self.root.title("Laptop Life-Saver — Setup")
        self.root.geometry("500x550")
        self.root.resizable(False, False)
        
        self.logo_path = logo_path
        self.config_path = config_path
        self.result = None
        
        # Style
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"))
        
        # Main Container
        self.container = ttk.Frame(self.root, padding="30")
        self.container.pack(fill="both", expand=True)
        
        self.show_privacy_screen()

    def show_privacy_screen(self):
        self._clear_container()
        
        # Logo
        try:
            img = Image.open(self.logo_path).resize((80, 80))
            self.photo = ImageTk.PhotoImage(img)
            ttk.Label(self.container, image=self.photo).pack(pady=10)
        except:
            pass
            
        ttk.Label(self.container, text="Your Privacy Shield", style="Header.TLabel").pack(pady=10)
        
        privacy_text = (
            "Laptop Life-Saver is designed to protect your device hardware. "
            "To build your trust, here is what we do and DON'T do:\n\n"
            "🛡️ WE MONITOR: CPU Temperature, Battery Health, Disk Usage, and Basic Performance.\n\n"
            "❌ WE NEVER ACCESS: Your personal files, photos, browser history, "
            "passwords, or private messages.\n\n"
            "This system exists only to ensure your laptop doesn't fail "
            "unexpectedly during your hard work."
        )
        
        lbl = tk.Label(
            self.container, 
            text=privacy_text, 
            wraplength=400, 
            justify="left", 
            font=("Segoe UI", 10),
            fg="#444"
        )
        lbl.pack(pady=20)
        
        btn_frame = ttk.Frame(self.container)
        btn_frame.pack(side="bottom", fill="x", pady=20)
        
        ttk.Button(btn_frame, text="I Understand & Accept", command=self.show_info_screen).pack(fill="x")

    def show_info_screen(self):
        self._clear_container()
        
        ttk.Label(self.container, text="Identify Your Device", style="Header.TLabel").pack(pady=10)
        ttk.Label(self.container, text="This helps the IT team assist you better.", foreground="gray").pack(pady=5)
        
        # Fields
        ttk.Label(self.container, text="Assigned User (Your Name):").pack(anchor="w", pady=(15, 0))
        self.ent_user = ttk.Entry(self.container, font=("Segoe UI", 11))
        self.ent_user.pack(fill="x", pady=5)
        
        ttk.Label(self.container, text="Your Email Address:").pack(anchor="w", pady=(10, 0))
        self.ent_email = ttk.Entry(self.container, font=("Segoe UI", 11))
        self.ent_email.pack(fill="x", pady=5)
        
        ttk.Label(self.container, text="Department / School:").pack(anchor="w", pady=(10, 0))
        self.ent_dept = ttk.Entry(self.container, font=("Segoe UI", 11))
        self.ent_dept.pack(fill="x", pady=5)
        
        ttk.Label(self.container, text="Asset Tag (Physical ID on laptop):").pack(anchor="w", pady=(10, 0))
        self.ent_tag = ttk.Entry(self.container, font=("Segoe UI", 11))
        self.ent_tag.pack(fill="x", pady=5)
        
        btn_frame = ttk.Frame(self.container)
        btn_frame.pack(side="bottom", fill="x", pady=20)
        
        ttk.Button(btn_frame, text="Finish Setup", command=self.save_and_exit).pack(fill="x")

    def _clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def save_and_exit(self):
        data = {
            "assigned_user": self.ent_user.get().strip(),
            "user_email": self.ent_email.get().strip(),
            "department": self.ent_dept.get().strip(),
            "asset_tag": self.ent_tag.get().strip(),
            "setup_complete": True
        }
        
        if not data["assigned_user"] or not data["user_email"]:
            messagebox.showwarning("Incomplete", "Please at least provide your name and email.")
            return
            
        try:
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=4)
            self.result = data
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save setup: {e}")

    def run(self):
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.root.mainloop()
        return self.result

def run_wizard(logo_path, config_path):
    wizard = SetupWizard(logo_path, config_path)
    return wizard.run()

if __name__ == "__main__":
    # Test run
    logo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Logo.png")
    run_wizard(logo, "user_config.json")
