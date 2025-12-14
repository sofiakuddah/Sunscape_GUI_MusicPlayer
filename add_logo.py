"""
Add logo to SUNSCAPE app
"""
import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add PIL import at the top
if 'from PIL import Image, ImageTk' not in content:
    # Find the import section
    import_pos = content.find('import tkinter as tk')
    if import_pos > 0:
        content = content[:import_pos] + 'from PIL import Image, ImageTk\n' + content[import_pos:]

# Update login screen to include logo
old_login = '''    def show_login_screen(self):
        """Show login screen"""
        self.clear_current_screen()
        self.current_screen_name = "login"
        
        center = tk.Frame(self.main_container, bg=self.COLORS['background'])
        center.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(center, text="🌅 SUNSCAPE", font=("Segoe UI", 32, "bold"), 
                foreground=self.COLORS['primary'], bg=self.COLORS['background']).pack(pady=(0, 5))
        
        tk.Label(center, text="Musik, senja, dan kamu.", font=("Segoe UI", 12, "italic"), 
                foreground=self.COLORS['accent'], bg=self.COLORS['background']).pack(pady=(0, 30))'''

new_login = '''    def show_login_screen(self):
        """Show login screen"""
        self.clear_current_screen()
        self.current_screen_name = "login"
        
        center = tk.Frame(self.main_container, bg=self.COLORS['background'])
        center.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "sunscape_logo.png")
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((200, 200), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(center, image=logo_photo, bg=self.COLORS['background'])
            logo_label.image = logo_photo  # Keep reference
            logo_label.pack(pady=(0, 15))
        except:
            # Fallback if logo not found
            tk.Label(center, text="🌅", font=("Segoe UI", 60), 
                    bg=self.COLORS['background']).pack(pady=(0, 15))
        
        tk.Label(center, text="SUNSCAPE", font=("Segoe UI", 32, "bold"), 
                foreground=self.COLORS['primary'], bg=self.COLORS['background']).pack(pady=(0, 5))
        
        tk.Label(center, text="Musik, senja, dan kamu.", font=("Segoe UI", 12, "italic"), 
                foreground=self.COLORS['accent'], bg=self.COLORS['background']).pack(pady=(0, 30))'''

content = content.replace(old_login, new_login)

# Update home screen header to include small logo
old_home_header = '''        # Header with Gradient Text feel (Primary Color)
        header_frame = ttk.Frame(frame, padding="20 20 20 8", style='TFrame')
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="🌅 SUNSCAPE", font=("Segoe UI", 22, "bold"), foreground=self.COLORS['primary']).pack(anchor='w')
        ttk.Label(header_frame, text="Musik, senja, dan kamu.", font=("Segoe UI", 11, "italic"), foreground=self.COLORS['accent']).pack(anchor='w')'''

new_home_header = '''        # Header with logo
        header_frame = ttk.Frame(frame, padding="15 15 15 8", style='TFrame')
        header_frame.pack(fill="x")
        
        header_content = tk.Frame(header_frame, bg=self.COLORS['background'])
        header_content.pack(fill="x")
        
        # Small logo
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "sunscape_logo.png")
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((50, 50), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(header_content, image=logo_photo, bg=self.COLORS['background'])
            logo_label.image = logo_photo
            logo_label.pack(side="left", padx=(0, 10))
        except:
            pass
        
        text_frame = tk.Frame(header_content, bg=self.COLORS['background'])
        text_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(text_frame, text="SUNSCAPE", font=("Segoe UI", 22, "bold"), 
                foreground=self.COLORS['primary'], bg=self.COLORS['background']).pack(anchor='w')
        tk.Label(text_frame, text="Musik, senja, dan kamu.", font=("Segoe UI", 11, "italic"), 
                foreground=self.COLORS['accent'], bg=self.COLORS['background']).pack(anchor='w')'''

content = content.replace(old_home_header, new_home_header)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Logo added to SUNSCAPE!")
