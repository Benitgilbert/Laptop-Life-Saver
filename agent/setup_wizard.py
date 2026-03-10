"""
setup_wizard.py — First-Run Setup Wizard
Laptop Life-Saver System | Nyanza District

A modern CustomTkinter GUI to collect user info and establish privacy trust.
"""

import customtkinter as ctk
import json
import os
from typing import Optional, Any
from PIL import Image

# Set the overall appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SetupWizard:
    def __init__(self, logo_path, config_path):
        self.root = ctk.CTk()
        self.root.title("Laptop Life-Saver — Setup")
        self.root.geometry("500x550")
        self.root.resizable(False, False)
        
        self.logo_path = logo_path
        self.config_path = config_path
        self.result: dict[str, Any] = {}
        
        # UI Attributes (typed for Pyre, never None)
        self.ent_user = ctk.CTkEntry(self.root)
        self.ent_email = ctk.CTkEntry(self.root)
        self.ent_dept = ctk.CTkEntry(self.root)
        self.ent_tag = ctk.CTkEntry(self.root)
        self.error_label = ctk.CTkLabel(self.root, text="")
        
        # Main Container
        self.container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=40, pady=40)
        
        self.show_privacy_screen()

    def _clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_privacy_screen(self):
        self._clear_container()
        
        # Logo
        try:
            img = Image.open(self.logo_path)
            logo_image = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
            logo_label = ctk.CTkLabel(self.container, image=logo_image, text="")
            logo_label.pack(pady=(0, 15))
        except Exception:
            pass
            
        header = ctk.CTkLabel(self.container, text="Your Privacy Shield", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"))
        header.pack(pady=(0, 15))
        
        intro = ctk.CTkLabel(
            self.container, 
            text="Laptop Life-Saver is designed to protect your device hardware. To build your trust, here is exactly what we do and don't do:",
            justify="center",
            wraplength=380,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="gray80"
        )
        intro.pack(pady=(0, 15))
        
        # We Monitor Card (Green Accent)
        monitor_frame = ctk.CTkFrame(self.container, fg_color="#1e293b", corner_radius=8)
        monitor_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(monitor_frame, text="🛡️ WE MONITOR", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#10b981").pack(anchor="w", padx=15, pady=(10, 5))
        
        # Monitor Checklist
        check_font = ctk.CTkFont(family="Segoe UI", size=12)
        ctk.CTkLabel(monitor_frame, text="✔️ CPU Temperature & Load", font=check_font).pack(anchor="w", padx=25, pady=(0, 2))
        ctk.CTkLabel(monitor_frame, text="✔️ Battery Health & Capacity", font=check_font).pack(anchor="w", padx=25, pady=2)
        ctk.CTkLabel(monitor_frame, text="✔️ Disk Storage Availability", font=check_font).pack(anchor="w", padx=25, pady=(2, 10))

        # We Never Access Card (Red Accent)
        never_frame = ctk.CTkFrame(self.container, fg_color="#1e293b", corner_radius=8)
        never_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(never_frame, text="❌ WE NEVER ACCESS", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#ef4444").pack(anchor="w", padx=15, pady=(10, 5))
        
        # Access Checklist
        ctk.CTkLabel(never_frame, text="✖️ Personal Files & Documents", font=check_font, text_color="gray80").pack(anchor="w", padx=25, pady=(0, 2))
        ctk.CTkLabel(never_frame, text="✖️ Browser History & Passwords", font=check_font, text_color="gray80").pack(anchor="w", padx=25, pady=2)
        ctk.CTkLabel(never_frame, text="✖️ Private Messages & Emails", font=check_font, text_color="gray80").pack(anchor="w", padx=25, pady=(2, 10))
        
        conclusion = ctk.CTkLabel(
            self.container, 
            text="This system exists purely to ensure your laptop doesn't fail unexpectedly during your daily work.",
            justify="center",
            wraplength=380,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="gray60"
        )
        conclusion.pack(pady=(0, 10))
        
        btn = ctk.CTkButton(
            self.container, 
            text="I Understand & Accept", 
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=40,
            command=self.show_info_screen
        )
        btn.pack(side="bottom", fill="x", pady=(20, 0))

    def show_info_screen(self):
        self._clear_container()
        
        header = ctk.CTkLabel(self.container, text="Identify Your Device", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"))
        header.pack(pady=(0, 5))
        
        sub = ctk.CTkLabel(self.container, text="This helps the Nyanza IT team assist you better.", font=ctk.CTkFont(family="Segoe UI", size=12), text_color="gray60")
        sub.pack(pady=(0, 15))
        
        # Helper to create styled forms
        def create_input(parent, label_text, placeholder=""):
            ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(anchor="w")
            entry = ctk.CTkEntry(parent, font=ctk.CTkFont(size=13), height=32, corner_radius=6, placeholder_text=placeholder)
            entry.pack(fill="x", pady=(2, 6))
            return entry

        self.ent_user = create_input(self.container, "Assigned User (Your Name):")
        self.ent_email = create_input(self.container, "Your Email Address:")
        
        # Optional: Add Supabase credentials if missing
        from .config import SUPABASE_URL, SUPABASE_KEY
        self.ent_url = None
        self.ent_key = None
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            ctk.CTkLabel(self.container, text="Cloud Configuration", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color="#3b82f6").pack(anchor="w", pady=(10, 5))
            self.ent_url = create_input(self.container, "Supabase Project URL:", "https://xxx.supabase.co")
            self.ent_key = create_input(self.container, "Supabase Service Role Key:", "eyJh...")

        self.ent_dept = create_input(self.container, "Department / School:")
        self.ent_tag = create_input(self.container, "Asset Tag (Physical ID on laptop):")
        
        # Error Label
        self.error_label = ctk.CTkLabel(self.container, text="", text_color="red", font=ctk.CTkFont(size=12))
        self.error_label.pack(pady=(5, 0))

        btn = ctk.CTkButton(
            self.container, 
            text="Finish Setup", 
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=40,
            fg_color="#10b981", # Tailwind Emerald 500
            hover_color="#059669", # Tailwind Emerald 600
            command=self.save_and_exit
        )
        btn.pack(side="bottom", fill="x", pady=(15, 0))

    def save_and_exit(self):
        if not self.ent_user or not self.ent_email or not self.ent_dept or not self.ent_tag or not self.error_label:
            return

        data = {
            "assigned_user": self.ent_user.get().strip(),
            "user_email": self.ent_email.get().strip(),
            "department": self.ent_dept.get().strip(),
            "asset_tag": self.ent_tag.get().strip(),
            "setup_complete": True
        }
        
        if self.ent_url and self.ent_key:
            data["supabase_url"] = self.ent_url.get().strip()
            data["supabase_key"] = self.ent_key.get().strip()
            
            # Simple validation
            if not data["supabase_url"].startswith("http"):
                self.error_label.configure(text="⚠️ Invalid Supabase URL")
                return
        
        if not data["assigned_user"] or not data["user_email"]:
            self.error_label.configure(text="⚠️ Please at least provide your name and email.")
            return
            
        try:
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=4)
            self.result = data
            self.root.destroy()
        except Exception as e:
            self.error_label.configure(text=f"Error saving: {e}")

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
