"""
Final polish script for SUNSCAPE UI
Improvements:
1. Optimize home screen layout (more compact)
2. Better admin screen organization
3. Consistent spacing throughout
4. Polish login screen
"""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Optimize Home Screen - make stats more compact
old_home_stats = '''        # Statistics Section
        stats_frame = ttk.LabelFrame(frame, text="📊 Listening Statistics", padding="20", style='TLabelframe')
        stats_frame.pack(fill="x", pady=10, padx=20)
        
        stats_inner = ttk.Frame(stats_frame, style='TFrame')
        stats_inner.pack(fill="x")
        
        # Left stats
        left_stats = ttk.Frame(stats_inner, style='TFrame')
        left_stats.pack(side="left", fill="x", expand=True)
        
        ttk.Label(left_stats, text="Total Lagu Dimainkan:", font=("Segoe UI", 11, "bold")).pack(anchor='w', pady=5)
        self.total_songs_label = ttk.Label(left_stats, text="0", font=("Segoe UI", 20, "bold"), foreground=self.COLORS['accent'])
        self.total_songs_label.pack(anchor='w', pady=(0, 15))
        
        ttk.Label(left_stats, text="Total Minutes Played:", font=("Segoe UI", 11, "bold")).pack(anchor='w', pady=5)
        self.total_minutes_label = ttk.Label(left_stats, text="0 min", font=("Segoe UI", 20, "bold"), foreground=self.COLORS['accent'])
        self.total_minutes_label.pack(anchor='w', pady=(0, 15))
        
        # Right stats
        right_stats = ttk.Frame(stats_inner, style='TFrame')
        right_stats.pack(side="right", fill="x", expand=True)
        
        ttk.Label(right_stats, text="Favorite Genre:", font=("Segoe UI", 11, "bold")).pack(anchor='w', pady=5)
        self.fav_genre_label = ttk.Label(right_stats, text="N/A", font=("Segoe UI", 20, "bold"), foreground=self.COLORS['accent'])
        self.fav_genre_label.pack(anchor='w', pady=(0, 15))
        
        ttk.Label(right_stats, text="Most Played Artist:", font=("Segoe UI", 11, "bold")).pack(anchor='w', pady=5)
        self.most_artist_label = ttk.Label(right_stats, text="N/A", font=("Segoe UI", 20, "bold"), foreground=self.COLORS['accent'])
        self.most_artist_label.pack(anchor='w', pady=(0, 15))'''

new_home_stats = '''        # Statistics Section - COMPACT
        stats_frame = ttk.LabelFrame(frame, text="📊 Stats", padding="12", style='TLabelframe')
        stats_frame.pack(fill="x", pady=8, padx=15)
        
        stats_inner = ttk.Frame(stats_frame, style='TFrame')
        stats_inner.pack(fill="x")
        
        # Left stats
        left_stats = ttk.Frame(stats_inner, style='TFrame')
        left_stats.pack(side="left", fill="x", expand=True)
        
        ttk.Label(left_stats, text="Songs Played:", font=("Segoe UI", 9, "bold")).pack(anchor='w', pady=2)
        self.total_songs_label = ttk.Label(left_stats, text="0", font=("Segoe UI", 16, "bold"), foreground=self.COLORS['accent'])
        self.total_songs_label.pack(anchor='w', pady=(0, 8))
        
        ttk.Label(left_stats, text="Minutes:", font=("Segoe UI", 9, "bold")).pack(anchor='w', pady=2)
        self.total_minutes_label = ttk.Label(left_stats, text="0 min", font=("Segoe UI", 16, "bold"), foreground=self.COLORS['accent'])
        self.total_minutes_label.pack(anchor='w', pady=(0, 8))
        
        # Right stats
        right_stats = ttk.Frame(stats_inner, style='TFrame')
        right_stats.pack(side="right", fill="x", expand=True)
        
        ttk.Label(right_stats, text="Fav Genre:", font=("Segoe UI", 9, "bold")).pack(anchor='w', pady=2)
        self.fav_genre_label = ttk.Label(right_stats, text="N/A", font=("Segoe UI", 16, "bold"), foreground=self.COLORS['accent'])
        self.fav_genre_label.pack(anchor='w', pady=(0, 8))
        
        ttk.Label(right_stats, text="Top Artist:", font=("Segoe UI", 9, "bold")).pack(anchor='w', pady=2)
        self.most_artist_label = ttk.Label(right_stats, text="N/A", font=("Segoe UI", 16, "bold"), foreground=self.COLORS['accent'])
        self.most_artist_label.pack(anchor='w', pady=(0, 8))'''

content = content.replace(old_home_stats, new_home_stats)

# 2. Optimize Quick Actions
old_quick = '''        # Quick Actions
        actions_frame = ttk.LabelFrame(frame, text="⚡ Quick Actions", padding="15", style='TLabelframe')
        actions_frame.pack(fill="x", pady=10, padx=20)
        
        action_buttons = ttk.Frame(actions_frame, style='TFrame')
        action_buttons.pack(fill="x", pady=10)
        
        ttk.Button(action_buttons, text="🎵 Play Random Song", command=self._play_random_song, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(action_buttons, text="⭐ Go to Playlists", command=self.show_playlist_screen, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(action_buttons, text="🔍 Search Songs", command=self.show_search_screen, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=5)'''

new_quick = '''        # Quick Actions - COMPACT
        actions_frame = ttk.LabelFrame(frame, text="⚡ Quick Access", padding="10", style='TLabelframe')
        actions_frame.pack(fill="x", pady=8, padx=15)
        
        action_buttons = ttk.Frame(actions_frame, style='TFrame')
        action_buttons.pack(fill="x", pady=5)
        
        ttk.Button(action_buttons, text="🎵 Random", command=self._play_random_song, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=3)
        ttk.Button(action_buttons, text="⭐ Playlists", command=self.show_playlist_screen, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=3)
        ttk.Button(action_buttons, text="🔍 Search", command=self.show_search_screen, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=3)'''

content = content.replace(old_quick, new_quick)

# 3. Optimize Recent Activity
old_recent = '''        # Recent Activity
        activity_frame = ttk.LabelFrame(frame, text="📝 Recent Activity", padding="15", style='TLabelframe')
        activity_frame.pack(fill="both", expand=True, pady=10, padx=20)
        
        ttk.Label(activity_frame, text="Lagu Terakhir Diputar:", font=("Segoe UI", 11, "bold")).pack(anchor='w', pady=(0, 10))
        
        self.recent_listbox = tk.Listbox(activity_frame, height=8, font=("Courier", 10), 
                                         selectbackground=self.COLORS['button'], selectforeground='white',
                                         bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0)
        self.recent_listbox.pack(fill="both", expand=True)
        
        # Scroll bar
        scroll = ttk.Scrollbar(activity_frame, orient="vertical", command=self.recent_listbox.yview)
        scroll.pack(side="right", fill="y")
        self.recent_listbox.config(yscrollcommand=scroll.set)'''

new_recent = '''        # Recent Activity - COMPACT
        activity_frame = ttk.LabelFrame(frame, text="📝 Recent", padding="10", style='TLabelframe')
        activity_frame.pack(fill="both", expand=True, pady=8, padx=15)
        
        ttk.Label(activity_frame, text="Recently played:", font=("Segoe UI", 8, "italic"), foreground=self.COLORS['text_secondary']).pack(anchor='w', pady=(0, 5))
        
        recent_container = ttk.Frame(activity_frame)
        recent_container.pack(fill="both", expand=True)
        
        self.recent_listbox = tk.Listbox(recent_container, height=8, font=("Courier", 8), 
                                         selectbackground=self.COLORS['button'], selectforeground='white',
                                         bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0)
        self.recent_listbox.pack(side="left", fill="both", expand=True)
        
        scroll = ttk.Scrollbar(recent_container, orient="vertical", command=self.recent_listbox.yview)
        scroll.pack(side="right", fill="y")
        self.recent_listbox.config(yscrollcommand=scroll.set)'''

content = content.replace(old_recent, new_recent)

# 4. Optimize Admin screen
old_admin_header = '''        header_frame = ttk.Frame(frame, padding="15 15 15 5", style='TFrame')
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="🔑 Control Panel Admin", font=("Segoe UI", 18, "bold"), foreground=self.COLORS['primary']).pack(anchor='w')
        ttk.Label(header_frame, text="Kelola Master Data Lagu. Semua perubahan sinkron otomatis ke User.", font=("Segoe UI", 10, "italic"), foreground=self.COLORS['text_secondary']).pack(anchor='w')'''

new_admin_header = '''        header_frame = ttk.Frame(frame, padding="10 10 10 5", style='TFrame')
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="🔑 Admin Panel", font=("Segoe UI", 16, "bold"), foreground=self.COLORS['primary']).pack(anchor='w')
        ttk.Label(header_frame, text="Manage library - changes sync to all users", font=("Segoe UI", 9, "italic"), foreground=self.COLORS['text_secondary']).pack(anchor='w')'''

content = content.replace(old_admin_header, new_admin_header)

# 5. Optimize admin buttons
old_admin_buttons = '''        action_frame = ttk.Frame(frame, padding="10 0", style='TFrame')
        action_frame.pack(fill="x", pady=10)
        ttk.Button(action_frame, text="➕ Tambah Lagu Baru", command=self.open_add_dialog, style='Fun.TButton').pack(side="left", padx=10)
        ttk.Button(action_frame, text="✏️ Edit Data Lagu", command=self.open_edit_dialog, style='Fun.TButton').pack(side="left", padx=10)
        ttk.Button(action_frame, text="❌ Hapus Lagu", command=self.delete_song_action, style='Fun.TButton').pack(side="left", padx=10)'''

new_admin_buttons = '''        action_frame = ttk.Frame(frame, padding="8 0", style='TFrame')
        action_frame.pack(fill="x", pady=8)
        ttk.Button(action_frame, text="➕ Add", command=self.open_add_dialog, style='Fun.TButton').pack(side="left", padx=5)
        ttk.Button(action_frame, text="✏️ Edit", command=self.open_edit_dialog, style='Fun.TButton').pack(side="left", padx=5)
        ttk.Button(action_frame, text="❌ Delete", command=self.delete_song_action, style='Fun.TButton').pack(side="left", padx=5)'''

content = content.replace(old_admin_buttons, new_admin_buttons)

# 6. Optimize admin list header
old_admin_list = '''        list_header_frame = ttk.Frame(frame, padding="10 5 10 0", style='TFrame')
        list_header_frame.pack(fill="x")
        ttk.Label(list_header_frame, text="ID | Judul | Penyanyi | Genre | Tahun | Durasi", font=("Courier", 10, "bold"), foreground=self.COLORS['accent']).pack(anchor="w")
        
        listbox_frame = ttk.Frame(frame, padding="10 5", style='TFrame')
        listbox_frame.pack(fill="both", expand=True)
        self.library_listbox = tk.Listbox(listbox_frame, height=15, font=("Courier", 10), bd=0, highlightthickness=0,'''

new_admin_list = '''        list_header_frame = ttk.Frame(frame, padding="8 5 8 0", style='TFrame')
        list_header_frame.pack(fill="x")
        ttk.Label(list_header_frame, text="ID | Title | Artist | Genre | Year | Duration", font=("Courier", 8, "bold"), foreground=self.COLORS['accent']).pack(anchor="w")
        
        listbox_frame = ttk.Frame(frame, padding="8 5", style='TFrame')
        listbox_frame.pack(fill="both", expand=True)
        self.library_listbox = tk.Listbox(listbox_frame, height=15, font=("Courier", 8), bd=0, highlightthickness=0,'''

content = content.replace(old_admin_list, new_admin_list)

# 7. Polish Profile section
old_profile = '''        # User Profile Section - Clean Layout
        profile_frame = ttk.LabelFrame(frame, text="👤  P R O F I L", padding="20", style='TLabelframe')
        profile_frame.pack(fill="x", pady=15, padx=25)
        
        ttk.Label(profile_frame, text=f"{self.current_user.username}", font=("Segoe UI", 24, "bold"), foreground='white').pack(anchor='w', pady=(0,5))
        ttk.Label(profile_frame, text=f"ID: {self.current_user.id}  •  Member Since: {datetime.now().strftime('%B %Y')}", 
                 font=("Segoe UI", 11), foreground=self.COLORS['text_secondary']).pack(anchor='w')'''

new_profile = '''        # User Profile Section - COMPACT
        profile_frame = ttk.LabelFrame(frame, text="👤 Profile", padding="12", style='TLabelframe')
        profile_frame.pack(fill="x", pady=8, padx=15)
        
        ttk.Label(profile_frame, text=f"{self.current_user.username}", font=("Segoe UI", 18, "bold"), foreground='white').pack(anchor='w', pady=(0,3))
        ttk.Label(profile_frame, text=f"ID: {self.current_user.id}  •  Since {datetime.now().strftime('%b %Y')}", 
                 font=("Segoe UI", 9), foreground=self.COLORS['text_secondary']).pack(anchor='w')'''

content = content.replace(old_profile, new_profile)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Final polish complete - UI optimized to maximum!")
