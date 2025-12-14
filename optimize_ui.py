"""
Script to optimize search and queue UI layout
Makes buttons more compact and organized
"""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the search_queue UI section
old_ui = '''    # ============= TAB 3: CARI & ANTRIAN UI =============
    def _setup_search_queue_ui(self, frame):
        """Setup SEARCH & QUEUE tab"""
        header_frame = ttk.Frame(frame, padding="15 15 15 5", style='TFrame')
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="🔍 Cari Lagu & Smart Queue", font=("Segoe UI", 18, "bold"), foreground=self.COLORS['primary']).pack(anchor='w')
        
        container = ttk.Frame(frame, style='TFrame')
        container.pack(fill="both", expand=True, padx=15, pady=10)
        
        # LEFT: Search section
        search_frame = ttk.LabelFrame(container, text="🔎 Pencarian Lagu", padding="15", style='TLabelframe')
        search_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        ttk.Label(search_frame, text="Kata Kunci:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.search_entry = ttk.Entry(search_frame, font=("Segoe UI", 11))
        self.search_entry.pack(fill="x", pady=(0, 10))
        
        search_by_var = tk.StringVar(value="title")
        ttk.Label(search_frame, text="Cari Berdasarkan:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        radio_frame = ttk.Frame(search_frame, style='TFrame')
        radio_frame.pack(anchor="w", pady=(0, 10))
        
        search_options = [("Judul", "title"), ("Artis", "artist"), ("ID", "id")]
        for text, value in search_options:
            ttk.Radiobutton(radio_frame, text=text, variable=search_by_var, value=value).pack(side="left", padx=(0, 15))
        
        ttk.Button(search_frame, text="🔍 CARI SEKARANG", command=lambda: self._search_song_action(self.search_entry.get(), search_by_var.get()), style='Fun.TButton').pack(fill="x", pady=(0, 15))
        
        ttk.Label(search_frame, text="📋 Hasil Pencarian:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 5))
        
        listbox_container = ttk.Frame(search_frame)
        listbox_container.pack(fill="both", expand=True, pady=(0, 10))
        self.search_listbox = tk.Listbox(listbox_container, height=12, font=("Courier", 10), 
                                         selectbackground=self.COLORS['button'], selectforeground='white',
                                         bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0)
        self.search_listbox.pack(side="left", fill="both", expand=True)
        search_scroll = ttk.Scrollbar(listbox_container, orient="vertical", command=self.search_listbox.yview)
        search_scroll.pack(side="right", fill="y")
        self.search_listbox.config(yscrollcommand=search_scroll.set)
        
        ttk.Label(search_frame, text="🎯 Aksi untuk Lagu Terpilih:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        
        self.target_playlist_var = tk.StringVar(value=list(self.current_user.playlists.keys())[0] if self.current_user.playlists else "My Playlist")
        
        playlist_select_frame = ttk.Frame(search_frame, style='TFrame')
        playlist_select_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(playlist_select_frame, text="Target:", font=("Segoe UI", 9)).pack(side="left", padx=(0, 5))
        self.playlist_dropdown = ttk.Combobox(playlist_select_frame, textvariable=self.target_playlist_var, values=list(self.current_user.playlists.keys()), state="readonly", width=20)
        self.playlist_dropdown.pack(side="left", fill="x", expand=True)
        
        ttk.Button(search_frame, text="▶️ Play dari Library", command=self._play_from_library, style='Fun.TButton').pack(fill="x", pady=3)
        ttk.Button(search_frame, text="❤️ Tambah ke Favorites", command=self._like_from_search, style='Fun.TButton').pack(fill="x", pady=3)
        ttk.Button(search_frame, text="➕ Tambah ke Playlist", command=self._add_to_selected_playlist_from_search, style='Fun.TButton').pack(fill="x", pady=3)
        
        # RIGHT: Smart Queue section
        queue_frame = ttk.LabelFrame(container, text="⏭️ Smart Queue", padding="15", style='TLabelframe')
        queue_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))
        
        ttk.Label(queue_frame, text="📝 Antrian Putar Selanjutnya:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 5))
        ttk.Label(queue_frame, text="Lagu-lagu di sini akan diputar setelah lagu saat ini selesai.", font=("Segoe UI", 9, "italic"), foreground=self.COLORS['text_secondary']).pack(anchor="w", pady=(0, 10))
        
        queue_listbox_container = ttk.Frame(queue_frame)
        queue_listbox_container.pack(fill="both", expand=True, pady=(0, 10))
        self.queue_listbox = tk.Listbox(queue_listbox_container, height=12, font=("Courier", 10), 
                                        selectbackground=self.COLORS['button'], selectforeground='white',
                                        bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0)
        self.queue_listbox.pack(side="left", fill="both", expand=True)
        queue_scroll = ttk.Scrollbar(queue_listbox_container, orient="vertical", command=self.queue_listbox.yview)
        queue_scroll.pack(side="right", fill="y")
        self.queue_listbox.config(yscrollcommand=queue_scroll.set)
        
        ttk.Label(queue_frame, text="🎯 Kelola Antrian:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        
        # FIX BUG #3: Tambah tombol Play dari Queue
        ttk.Button(queue_frame, text="▶️ Play dari Queue", command=self._play_from_queue, style='Fun.TButton').pack(fill="x", pady=3)
        ttk.Button(queue_frame, text="⬆️ Play Next (Tambah ke Awal)", command=self._add_to_queue_next, style='Fun.TButton').pack(fill="x", pady=3)
        ttk.Button(queue_frame, text="⬇️ Play Later (Tambah ke Akhir)", command=self._add_to_queue_later, style='Fun.TButton').pack(fill="x", pady=3)
        ttk.Button(queue_frame, text="🗑️ Clear Queue (Kosongkan)", command=self._clear_queue, style='Fun.TButton').pack(fill="x", pady=3)
        ttk.Button(queue_frame, text="💾 Save as Playlist", command=self._save_queue_as_playlist, style='Fun.TButton').pack(fill="x", pady=3)'''

new_ui = '''    # ============= TAB 3: CARI & ANTRIAN UI =============
    def _setup_search_queue_ui(self, frame):
        """Setup SEARCH & QUEUE tab - COMPACT VERSION"""
        header_frame = ttk.Frame(frame, padding="10 10 10 5", style='TFrame')
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="🔍 Search & Queue", font=("Segoe UI", 16, "bold"), foreground=self.COLORS['primary']).pack(anchor='w')
        
        container = ttk.Frame(frame, style='TFrame')
        container.pack(fill="both", expand=True, padx=10, pady=8)
        
        # LEFT: Search section - COMPACT
        search_frame = ttk.LabelFrame(container, text="🔎 Search", padding="10", style='TLabelframe')
        search_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Compact search input
        search_input = ttk.Frame(search_frame, style='TFrame')
        search_input.pack(fill="x", pady=(0, 6))
        
        self.search_entry = ttk.Entry(search_input, font=("Segoe UI", 9), width=20)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 3))
        
        search_by_var = tk.StringVar(value="title")
        tk.Radiobutton(search_input, text="Title", variable=search_by_var, value="title",
                      bg=self.COLORS['background'], fg=self.COLORS['text'], selectcolor=self.COLORS['button'],
                      font=("Segoe UI", 7)).pack(side="left", padx=1)
        tk.Radiobutton(search_input, text="Artist", variable=search_by_var, value="artist",
                      bg=self.COLORS['background'], fg=self.COLORS['text'], selectcolor=self.COLORS['button'],
                      font=("Segoe UI", 7)).pack(side="left", padx=1)
        
        search_btn = ttk.Button(search_input, text="🔍", 
                               command=lambda: self._search_song_action(self.search_entry.get(), search_by_var.get()), 
                               style='Fun.TButton', width=3)
        search_btn.pack(side="left", padx=2)
        ToolTip(search_btn, "Search")
        
        # Results
        ttk.Label(search_frame, text="Results:", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 2))
        
        listbox_container = ttk.Frame(search_frame)
        listbox_container.pack(fill="both", expand=True, pady=(0, 6))
        self.search_listbox = tk.Listbox(listbox_container, height=9, font=("Courier", 8), 
                                         selectbackground=self.COLORS['button'], selectforeground='white',
                                         bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0)
        self.search_listbox.pack(side="left", fill="both", expand=True)
        search_scroll = ttk.Scrollbar(listbox_container, orient="vertical", command=self.search_listbox.yview)
        search_scroll.pack(side="right", fill="y")
        self.search_listbox.config(yscrollcommand=search_scroll.set)
        
        # Actions - COMPACT
        ttk.Label(search_frame, text="Actions:", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(3, 2))
        
        # Playlist selector
        self.target_playlist_var = tk.StringVar(value=list(self.current_user.playlists.keys())[0] if self.current_user.playlists else "My Playlist")
        
        pl_frame = ttk.Frame(search_frame, style='TFrame')
        pl_frame.pack(fill="x", pady=(0, 3))
        ttk.Label(pl_frame, text="To:", font=("Segoe UI", 7)).pack(side="left", padx=(0, 2))
        self.playlist_dropdown = ttk.Combobox(pl_frame, textvariable=self.target_playlist_var, 
                                             values=list(self.current_user.playlists.keys()), 
                                             state="readonly", width=12, font=("Segoe UI", 7))
        self.playlist_dropdown.pack(side="left", fill="x", expand=True)
        
        # Buttons in rows - COMPACT
        act1 = ttk.Frame(search_frame, style='TFrame')
        act1.pack(fill="x", pady=1)
        
        b1 = ttk.Button(act1, text="▶️", command=self._play_from_library, style='Fun.TButton', width=3)
        b1.pack(side="left", padx=1)
        ToolTip(b1, "Play")
        
        b2 = ttk.Button(act1, text="❤️", command=self._like_from_search, style='Fun.TButton', width=3)
        b2.pack(side="left", padx=1)
        ToolTip(b2, "Favorite")
        
        b3 = ttk.Button(act1, text="➕ Add to Playlist", command=self._add_to_selected_playlist_from_search, style='Fun.TButton')
        b3.pack(side="left", padx=1, fill="x", expand=True)
        
        # RIGHT: Queue - COMPACT
        queue_frame = ttk.LabelFrame(container, text="⏭️ Queue", padding="10", style='TLabelframe')
        queue_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        ttk.Label(queue_frame, text="Next up:", font=("Segoe UI", 7, "italic"), foreground=self.COLORS['text_secondary']).pack(anchor="w", pady=(0, 3))
        
        queue_listbox_container = ttk.Frame(queue_frame)
        queue_listbox_container.pack(fill="both", expand=True, pady=(0, 6))
        self.queue_listbox = tk.Listbox(queue_listbox_container, height=9, font=("Courier", 8), 
                                        selectbackground=self.COLORS['button'], selectforeground='white',
                                        bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0)
        self.queue_listbox.pack(side="left", fill="both", expand=True)
        queue_scroll = ttk.Scrollbar(queue_listbox_container, orient="vertical", command=self.queue_listbox.yview)
        queue_scroll.pack(side="right", fill="y")
        self.queue_listbox.config(yscrollcommand=queue_scroll.set)
        
        ttk.Label(queue_frame, text="Manage:", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(3, 2))
        
        # Queue buttons - COMPACT in rows
        q1 = ttk.Frame(queue_frame, style='TFrame')
        q1.pack(fill="x", pady=1)
        
        qb1 = ttk.Button(q1, text="▶️", command=self._play_from_queue, style='Fun.TButton', width=3)
        qb1.pack(side="left", padx=1)
        ToolTip(qb1, "Play")
        
        qb2 = ttk.Button(q1, text="⬆️ Next", command=self._add_to_queue_next, style='Fun.TButton')
        qb2.pack(side="left", padx=1, fill="x", expand=True)
        ToolTip(qb2, "Play next")
        
        qb3 = ttk.Button(q1, text="⬇️ Later", command=self._add_to_queue_later, style='Fun.TButton')
        qb3.pack(side="left", padx=1, fill="x", expand=True)
        ToolTip(qb3, "Play later")
        
        q2 = ttk.Frame(queue_frame, style='TFrame')
        q2.pack(fill="x", pady=1)
        
        qb4 = ttk.Button(q2, text="🗑️ Clear", command=self._clear_queue, style='Fun.TButton')
        qb4.pack(side="left", padx=1, fill="x", expand=True)
        ToolTip(qb4, "Clear queue")
        
        qb5 = ttk.Button(q2, text="💾 Save as Playlist", command=self._save_queue_as_playlist, style='Fun.TButton')
        qb5.pack(side="left", padx=1, fill="x", expand=True)
        ToolTip(qb5, "Save as playlist")'''

content = content.replace(old_ui, new_ui)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Search & Queue UI optimized - much more compact!")
