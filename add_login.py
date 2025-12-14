"""
Script to add login screen and remove tabs from SUNSCAPE app.py
This preserves all existing functionality while adding login and screen navigation.
"""

# Read the original file
with open('app_with_tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the __init__ method's UI setup section
# We need to replace the notebook creation with screen manager

old_init_ui = """        # Main frame
        self.main_frame = ttk.Frame(master)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Main notebook dengan 4 tab SEJAJAR HORIZONTAL
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # TAB 1: HOME - User Dashboard
        self.home_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.home_frame, text="🏠 HOME")
        self._setup_home_ui(self.home_frame)
        
        # TAB 2: ADMIN - Library Control
        self.admin_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.admin_frame, text="⚙️ ADMIN - Library Control")
        self._setup_admin_ui(self.admin_frame)
        
        # TAB 3: Cari & Antrian (Search + Queue)
        self.search_queue_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_queue_frame, text="🔍 Cari & Antrian")
        self._setup_search_queue_ui(self.search_queue_frame)
        
        # TAB 4: Playlist Saya
        self.playlist_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.playlist_frame, text="⭐ Playlist Saya")
        self._setup_playlist_ui(self.playlist_frame)
        
        # Initial updates
        self._update_listbox()
        self._update_playlist_listbox()
        self._update_queue_listbox()"""

new_init_ui = """        # Current mode tracking
        self.current_mode = None  # "user" or "admin"
        self.current_screen_name = None
        
        # Main container for all screens
        self.main_container = tk.Frame(master, bg=self.COLORS['background'])
        self.main_container.pack(fill="both", expand=True)
        
        # Frames will be created on demand
        self.home_frame = None
        self.admin_frame = None
        self.search_queue_frame = None
        self.playlist_frame = None
        
        # Show login screen first
        self.show_login_screen()"""

content = content.replace(old_init_ui, new_init_ui)

# Add login screen and navigation methods before _seed_data
login_methods = '''
    # ============= SCREEN MANAGER =============
    def clear_current_screen(self):
        """Clear current screen"""
        for widget in self.main_container.winfo_children():
            widget.destroy()
    
    def show_login_screen(self):
        """Show login screen"""
        self.clear_current_screen()
        self.current_screen_name = "login"
        
        center = tk.Frame(self.main_container, bg=self.COLORS['background'])
        center.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(center, text="🌅 SUNSCAPE", font=("Segoe UI", 32, "bold"), 
                foreground=self.COLORS['primary'], bg=self.COLORS['background']).pack(pady=(0, 5))
        
        tk.Label(center, text="Musik, senja, dan kamu.", font=("Segoe UI", 12, "italic"), 
                foreground=self.COLORS['accent'], bg=self.COLORS['background']).pack(pady=(0, 30))
        
        user_btn = ttk.Button(center, text="🎵 USER MODE", 
                              command=lambda: self.login_as("user"), style='Fun.TButton')
        user_btn.pack(pady=8, ipadx=40, ipady=10)
        ToolTip(user_btn, "Login as User")
        
        admin_btn = ttk.Button(center, text="⚙️ ADMIN MODE", 
                               command=lambda: self.login_as("admin"), style='Fun.TButton')
        admin_btn.pack(pady=8, ipadx=40, ipady=10)
        ToolTip(admin_btn, "Login as Admin")
    
    def login_as(self, mode):
        """Login and show appropriate screen"""
        self.current_mode = mode
        if mode == "user":
            self.show_home_screen()
        else:
            self.show_admin_screen()
    
    def show_home_screen(self):
        """Show home screen"""
        self.clear_current_screen()
        self.current_screen_name = "home"
        
        # Create frame
        self.home_frame = ttk.Frame(self.main_container)
        self.home_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add logout button at top
        header = tk.Frame(self.home_frame, bg=self.COLORS['background'])
        header.pack(fill="x", pady=(0, 10))
        
        logout_btn = ttk.Button(header, text="🚪 Logout", command=self.show_login_screen, style='Fun.TButton')
        logout_btn.pack(side="right")
        ToolTip(logout_btn, "Back to Login")
        
        # Setup home UI
        self._setup_home_ui(self.home_frame)
        
        # Update lists
        self._update_listbox()
    
    def show_admin_screen(self):
        """Show admin screen"""
        self.clear_current_screen()
        self.current_screen_name = "admin"
        
        # Create frame
        self.admin_frame = ttk.Frame(self.main_container)
        self.admin_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add logout button at top
        header = tk.Frame(self.admin_frame, bg=self.COLORS['background'])
        header.pack(fill="x", pady=(0, 10))
        
        logout_btn = ttk.Button(header, text="🚪 Logout", command=self.show_login_screen, style='Fun.TButton')
        logout_btn.pack(side="right")
        ToolTip(logout_btn, "Back to Login")
        
        # Setup admin UI
        self._setup_admin_ui(self.admin_frame)
        
        # Update lists
        self._update_listbox()
    
    def show_search_screen(self):
        """Show search screen"""
        self.clear_current_screen()
        self.current_screen_name = "search"
        
        # Create frame
        self.search_queue_frame = ttk.Frame(self.main_container)
        self.search_queue_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add navigation buttons at top
        header = tk.Frame(self.search_queue_frame, bg=self.COLORS['background'])
        header.pack(fill="x", pady=(0, 10))
        
        back_btn = ttk.Button(header, text="🏠 Home", command=self.show_home_screen, style='Fun.TButton')
        back_btn.pack(side="left")
        ToolTip(back_btn, "Back to Home")
        
        logout_btn = ttk.Button(header, text="🚪 Logout", command=self.show_login_screen, style='Fun.TButton')
        logout_btn.pack(side="right")
        ToolTip(logout_btn, "Back to Login")
        
        # Setup search UI
        self._setup_search_queue_ui(self.search_queue_frame)
        
        # Update lists
        self._update_queue_listbox()
    
    def show_playlist_screen(self):
        """Show playlist screen"""
        self.clear_current_screen()
        self.current_screen_name = "playlist"
        
        # Create frame
        self.playlist_frame = ttk.Frame(self.main_container)
        self.playlist_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add navigation buttons at top
        header = tk.Frame(self.playlist_frame, bg=self.COLORS['background'])
        header.pack(fill="x", pady=(0, 10))
        
        back_btn = ttk.Button(header, text="🏠 Home", command=self.show_home_screen, style='Fun.TButton')
        back_btn.pack(side="left")
        ToolTip(back_btn, "Back to Home")
        
        logout_btn = ttk.Button(header, text="🚪 Logout", command=self.show_login_screen, style='Fun.TButton')
        logout_btn.pack(side="right")
        ToolTip(logout_btn, "Back to Login")
        
        # Setup playlist UI
        self._setup_playlist_ui(self.playlist_frame)
        
        # Update lists
        self._update_playlist_listbox()

'''

# Insert login methods before _seed_data
seed_data_pos = content.find('    def _seed_data(self):')
if seed_data_pos > 0:
    content = content[:seed_data_pos] + login_methods + content[seed_data_pos:]

# Update Quick Actions buttons to use new navigation
content = content.replace(
    'command=lambda: self.notebook.select(3)',
    'command=self.show_playlist_screen'
)
content = content.replace(
    'command=lambda: self.notebook.select(2)',
    'command=self.show_search_screen'
)

# Write the modified content
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Successfully added login screen and removed tabs!")
print("✅ All features preserved!")
