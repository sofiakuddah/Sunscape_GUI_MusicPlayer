"""
Script to optimize playlist UI layout
Makes it compact like search/queue
"""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace playlist UI
old_playlist = '''    # ============= TAB 4: PLAYLIST UI =============
    def _setup_playlist_ui(self, frame):
        """Setup PLAYLIST tab"""
        header_frame = ttk.Frame(frame, padding="15 15 15 5", style='TFrame')
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="⭐ Playlist Saya", font=("Segoe UI", 18, "bold"), foreground=self.COLORS['primary']).pack(anchor='w')
        ttk.Label(header_frame, text=f"Kelola koleksi musik Anda - User: {self.current_user.username}", font=("Segoe UI", 10, "italic"), foreground=self.COLORS['text_secondary']).pack(anchor='w')
        
        container = ttk.Frame(frame, style='TFrame')
        container.pack(fill="both", expand=True, padx=20, pady=10)
        
        selector_frame = ttk.LabelFrame(container, text="📚 Pilih Playlist", padding="15", style='TLabelframe')
        selector_frame.pack(fill="x", pady=(0, 15))
        
        selector_inner = ttk.Frame(selector_frame, style='TFrame')
        selector_inner.pack(fill="x")
        
        ttk.Label(selector_inner, text="Playlist Aktif:", font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 15))
        self.active_playlist_var = tk.StringVar(value=self.current_playlist_name)
        self.active_playlist_dropdown = ttk.Combobox(selector_inner, textvariable=self.active_playlist_var, values=list(self.current_user.playlists.keys()), state="readonly", font=("Segoe UI", 11), width=35)
        self.active_playlist_dropdown.pack(side="left", fill="x", expand=True)
        self.active_playlist_dropdown.bind("<<ComboboxSelected>>", self._switch_playlist)
        
        content_frame = ttk.LabelFrame(container, text="🎵 Daftar Lagu", padding="15", style='TLabelframe')
        content_frame.pack(fill="both", expand=True)
        
        ttk.Label(content_frame, text="Lagu-lagu dalam playlist ini:", font=("Segoe UI", 10), foreground=self.COLORS['text_secondary']).pack(anchor="w", pady=(0, 8))
        
        listbox_container = ttk.Frame(content_frame)
        listbox_container.pack(fill="both", expand=True, pady=(0, 15))
        self.playlist_listbox = tk.Listbox(listbox_container, height=15, font=("Courier", 10), 
                                           selectbackground=self.COLORS['button'], selectforeground='white',
                                           bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0)
        self.playlist_listbox.pack(side="left", fill="both", expand=True)
        playlist_scroll = ttk.Scrollbar(listbox_container, orient="vertical", command=self.playlist_listbox.yview)
        playlist_scroll.pack(side="right", fill="y")
        self.playlist_listbox.config(yscrollcommand=playlist_scroll.set)
        
        ttk.Label(content_frame, text="🎯 Kontrol Lagu:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 8))
        
        control_frame1 = ttk.Frame(content_frame, style='TFrame')
        control_frame1.pack(fill="x", pady=(0, 5))
        ttk.Button(control_frame1, text="▲ Pindah Naik", command=self._move_song_up, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(control_frame1, text="▼ Pindah Turun", command=self._move_song_down, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=(4, 4))
        ttk.Button(control_frame1, text="▶️ Play Lagu Ini", command=self._play_selected_from_playlist, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=(4, 0))
        
        control_frame2 = ttk.Frame(content_frame, style='TFrame')
        control_frame2.pack(fill="x", pady=(0, 5))
        ttk.Button(control_frame2, text="🗑️ Hapus dari Playlist", command=self._remove_from_playlist, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(control_frame2, text="❤️ Tambah ke Favorites", command=self._like_from_playlist, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=(4, 0))

        # FIX: Tambahan Tombol Control Playlist (Shuffle, Repeat, Sort, Delete Playlist)
        control_frame3 = ttk.Frame(content_frame, style='TFrame')
        control_frame3.pack(fill="x", pady=(0, 5))
        
        self.btn_shuffle = ttk.Button(control_frame3, text="🔀 Shuffle: OFF", command=self._toggle_shuffle, style='Fun.TButton')
        self.btn_shuffle.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ToolTip(self.btn_shuffle, "Acak urutan lagu dalam playlist")
        
        self.btn_repeat = ttk.Button(control_frame3, text="🔁 Repeat: OFF", command=self._cycle_repeat, style='Fun.TButton')
        self.btn_repeat.pack(side="left", fill="x", expand=True, padx=(4, 4))
        ToolTip(self.btn_repeat, "Ulangi playlist dari awal setelah selesai")
        
        control_frame4 = ttk.Frame(content_frame, style='TFrame')
        control_frame4.pack(fill="x", pady=(0, 5))
        
        # Sort by ID button with tooltip
        sort_btn = ttk.Button(control_frame4, text="🔢 Sort All Songs by ID", command=self._sort_playlist_by_id, style='Fun.TButton')
        sort_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ToolTip(sort_btn, "Mengurutkan SEMUA lagu dalam playlist berdasarkan ID")
        
        # Delete playlist button with tooltip
        delete_btn = ttk.Button(control_frame4, text="❌ Delete Entire Playlist", command=self._delete_current_playlist, style='Fun.TButton')
        delete_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ToolTip(delete_btn, "Menghapus SELURUH playlist yang dipilih (bukan hanya lagu)")'''

new_playlist = '''    # ============= TAB 4: PLAYLIST UI =============
    def _setup_playlist_ui(self, frame):
        """Setup PLAYLIST tab - COMPACT VERSION"""
        header_frame = ttk.Frame(frame, padding="10 10 10 5", style='TFrame')
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="⭐ Playlists", font=("Segoe UI", 16, "bold"), foreground=self.COLORS['primary']).pack(anchor='w')
        
        container = ttk.Frame(frame, style='TFrame')
        container.pack(fill="both", expand=True, padx=10, pady=8)
        
        # Compact selector
        selector_frame = ttk.Frame(container, style='TFrame')
        selector_frame.pack(fill="x", pady=(0, 8))
        
        ttk.Label(selector_frame, text="Playlist:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 5))
        self.active_playlist_var = tk.StringVar(value=self.current_playlist_name)
        self.active_playlist_dropdown = ttk.Combobox(selector_frame, textvariable=self.active_playlist_var, 
                                                     values=list(self.current_user.playlists.keys()), 
                                                     state="readonly", font=("Segoe UI", 9), width=25)
        self.active_playlist_dropdown.pack(side="left", fill="x", expand=True)
        self.active_playlist_dropdown.bind("<<ComboboxSelected>>", self._switch_playlist)
        
        # Songs list
        ttk.Label(container, text="Songs:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 3))
        
        listbox_container = ttk.Frame(container)
        listbox_container.pack(fill="both", expand=True, pady=(0, 8))
        self.playlist_listbox = tk.Listbox(listbox_container, height=12, font=("Courier", 8), 
                                           selectbackground=self.COLORS['button'], selectforeground='white',
                                           bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0)
        self.playlist_listbox.pack(side="left", fill="both", expand=True)
        playlist_scroll = ttk.Scrollbar(listbox_container, orient="vertical", command=self.playlist_listbox.yview)
        playlist_scroll.pack(side="right", fill="y")
        self.playlist_listbox.config(yscrollcommand=playlist_scroll.set)
        
        # Compact controls
        ttk.Label(container, text="Controls:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(3, 2))
        
        # Row 1: Move & Play
        c1 = ttk.Frame(container, style='TFrame')
        c1.pack(fill="x", pady=1)
        
        b1 = ttk.Button(c1, text="▲", command=self._move_song_up, style='Fun.TButton', width=3)
        b1.pack(side="left", padx=1)
        ToolTip(b1, "Move up")
        
        b2 = ttk.Button(c1, text="▼", command=self._move_song_down, style='Fun.TButton', width=3)
        b2.pack(side="left", padx=1)
        ToolTip(b2, "Move down")
        
        b3 = ttk.Button(c1, text="▶️ Play", command=self._play_selected_from_playlist, style='Fun.TButton')
        b3.pack(side="left", padx=1, fill="x", expand=True)
        ToolTip(b3, "Play this song")
        
        b4 = ttk.Button(c1, text="🗑️", command=self._remove_from_playlist, style='Fun.TButton', width=3)
        b4.pack(side="left", padx=1)
        ToolTip(b4, "Remove from playlist")
        
        b5 = ttk.Button(c1, text="❤️", command=self._like_from_playlist, style='Fun.TButton', width=3)
        b5.pack(side="left", padx=1)
        ToolTip(b5, "Add to Favorites")
        
        # Row 2: Shuffle & Repeat
        c2 = ttk.Frame(container, style='TFrame')
        c2.pack(fill="x", pady=1)
        
        self.btn_shuffle = ttk.Button(c2, text="🔀 Shuffle: OFF", command=self._toggle_shuffle, style='Fun.TButton')
        self.btn_shuffle.pack(side="left", fill="x", expand=True, padx=1)
        ToolTip(self.btn_shuffle, "Shuffle playlist")
        
        self.btn_repeat = ttk.Button(c2, text="🔁 Repeat: OFF", command=self._cycle_repeat, style='Fun.TButton')
        self.btn_repeat.pack(side="left", fill="x", expand=True, padx=1)
        ToolTip(self.btn_repeat, "Repeat playlist")
        
        # Row 3: Sort & Delete
        c3 = ttk.Frame(container, style='TFrame')
        c3.pack(fill="x", pady=1)
        
        sort_btn = ttk.Button(c3, text="🔢 Sort by ID", command=self._sort_playlist_by_id, style='Fun.TButton')
        sort_btn.pack(side="left", fill="x", expand=True, padx=1)
        ToolTip(sort_btn, "Sort all songs by ID")
        
        delete_btn = ttk.Button(c3, text="❌ Delete Playlist", command=self._delete_current_playlist, style='Fun.TButton')
        delete_btn.pack(side="left", fill="x", expand=True, padx=1)
        ToolTip(delete_btn, "Delete entire playlist")'''

content = content.replace(old_playlist, new_playlist)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Playlist UI optimized - compact and organized!")
