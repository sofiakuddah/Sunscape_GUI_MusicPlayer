import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
import random
import re
from datetime import datetime

# Import dari models dan utils menggunakan import relatif
from ..models.doubly_linked_list import DoublyLinkedList
from ..models.song import Song
from ..models.playlist import Playlist
from ..models.user import UserManager, PlayerStack, SmartQueue
from ..utils.helpers import levenshtein_distance, fisher_yates_shuffle


class ToolTip:
    """Tooltip class untuk menampilkan tooltip saat hover"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        try:
            x = self.widget.winfo_rootx() + 25
            y = self.widget.winfo_rooty() + 25
            
            self.tooltip = tk.Toplevel(self.widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip, text=self.text, background="#FFE5B4", 
                            foreground="#000000", relief="solid", borderwidth=1,
                            font=("Segoe UI", 9), padx=5, pady=3)
            label.pack()
        except:
            pass
    
    def hide_tooltip(self, event=None):
        if self.tooltip:
            try:
                self.tooltip.destroy()
            except:
                pass
            self.tooltip = None


class FloatingPlayerWindow:
    """Floating player window yang muncul saat lagu diputar"""
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = None
        self.timer_id = None
        self.elapsed_seconds = 0
        self.total_seconds = 0
        
    def create_window(self):
        """Buat floating player window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus()
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("🌅 SUNSCAPE Player")
        self.window.geometry("400x350")
        self.window.resizable(False, False)
        self.window.attributes('-topmost', True)
        self.window.configure(bg=self.app.COLORS['background'])  # Deep Night Blue
        
        # Title
        title_frame = ttk.Frame(self.window, style='Card.TFrame')
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.song_title = tk.Label(self.window, text="Memilih Lagu...", font=("Segoe UI", 16, "bold"), 
                                    foreground=self.app.COLORS['accent'], bg=self.app.COLORS['background'], wraplength=350, justify="center")
        self.song_title.pack(fill="x", pady=(0, 5))
        
        self.song_artist = tk.Label(self.window, text="", font=("Segoe UI", 12), 
                                     foreground=self.app.COLORS['text'], bg=self.app.COLORS['background'], wraplength=350)
        self.song_artist.pack(fill="x", pady=(0, 20))
        
        # Progress bar
        progress_frame = ttk.Frame(self.window, style='Card.TFrame')
        progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                             maximum=100, length=360, mode='determinate')
        self.progress_bar.pack(fill="x", pady=(0, 10))
        
        # Time display
        time_frame = ttk.Frame(self.window, style='Card.TFrame')
        time_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.time_label = tk.Label(time_frame, text="0:00 / 0:00", font=("Segoe UI", 11, "bold"), 
                                    foreground=self.app.COLORS['primary'], bg=self.app.COLORS['background'])
        self.time_label.pack()
        
        # Control buttons (Icon-only dengan Tooltips)
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill="x", padx=20, pady=15)
        
        # Previous button
        self.prev_button = ttk.Button(control_frame, text="⏮️", 
                                       command=self.app._prev_song, width=5)
        self.prev_button.pack(side="left", padx=5)
        ToolTip(self.prev_button, "Previous Song")
        
        # Play/Pause button
        self.play_pause_button = ttk.Button(control_frame, text="⏸️", 
                                             command=self.app._toggle_play_stop, width=5)
        self.play_pause_button.pack(side="left", padx=5)
        ToolTip(self.play_pause_button, "Pause / Play")
        
        # Next button
        self.next_button = ttk.Button(control_frame, text="⏭️", 
                                       command=self.app._next_song, width=5)
        self.next_button.pack(side="left", padx=5)
        ToolTip(self.next_button, "Next Song")
# FIX: Buttons Shuffle & Repeat dipindah ke Playlist UI (Requirement User)

        
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
    def close_window(self):
        """Tutup window dengan benar"""
        if self.timer_id:
            self.window.after_cancel(self.timer_id)
        if self.window and self.window.winfo_exists():
            self.window.destroy()
        self.window = None
    
    def update_display(self, song: Optional[Song], is_playing: bool):
        """Update tampilan player"""
        if not self.window or not self.window.winfo_exists():
            return
        
        if song:
            self.song_title.config(text=song.title)
            self.song_artist.config(text=f"{song.artist}")
            
            # Parse duration dengan benar
            self.total_seconds = self._parse_duration(song.duration)
            
            # Update play button icon
            self.play_pause_button.config(text="⏸️" if is_playing else "▶️")
        
        # FIX: Remove mode updates from here since buttons are gone

    
    def _parse_duration(self, duration: str) -> int:
        """Parse duration string ke detik"""
        try:
            parts = duration.split(":")
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
            return 0
        except:
            return 0
    
    def start_timer(self):
        """Mulai timer untuk update progress"""
        self.stop_timer()  # FIX BUG: Stop timer sebelumnya agar speed tidak double
        self.elapsed_seconds = 0
        self._update_timer()
    
    def _update_timer(self):
        """Update progress bar setiap 1 DETIK (1000ms)"""
        if not self.window or not self.window.winfo_exists():
            return
        
        if self.app.is_playing:
            self.elapsed_seconds += 1
            if self.total_seconds > 0:
                progress = (self.elapsed_seconds / self.total_seconds) * 100
                self.progress_var.set(progress)
                
                # Update time display
                elapsed_min = self.elapsed_seconds // 60
                elapsed_sec = self.elapsed_seconds % 60
                total_min = self.total_seconds // 60
                total_sec = self.total_seconds % 60
                
                time_text = f"{elapsed_min}:{elapsed_sec:02d} / {total_min}:{total_sec:02d}"
                self.time_label.config(text=time_text)
                
                # Auto next jika lagu selesai
                if self.elapsed_seconds >= self.total_seconds:
                    self.app._next_song()  # Panggil next song app
                    return
        
        
        # UPDATE SETIAP 1000ms = 1 DETIK (FIX: dulu 100ms, sekarang 1000ms)
        self.timer_id = self.window.after(1000, self._update_timer)
    
    def stop_timer(self):
        """Stop timer"""
        if self.timer_id:
            self.window.after_cancel(self.timer_id)
            self.timer_id = None


class MusicPlayerApp:
    def __init__(self, master):
        self.master = master
        master.title("🌅 SUNSCAPE: Lanskap Musik dalam Cahaya Senja")
        master.geometry("1100x800")
        
        # THEME: SUNSCAPE (Sunset Gradient Premium)
        # Palette: Sunset Gradient Orange → Pink → Purple
        self.COLORS = {
            'primary': '#FF6B35',      # Sunset Orange - Highlight Utama
            'secondary': '#9D4EDD',    # Deep Purple - Container/Cards
            'accent': '#FF69B4',       # Hot Pink - Focus/Active
            'background': '#1A0B2E',   # Deep Indigo (Langit Malam Gelap) - Main BG
            'text': '#FFFFFF',         # Putih Bersih - Teks Utama
            'text_secondary': '#D1C4E9', # Lavender Soft - Teks Deskripsi
            'card': '#2D1B4E',         # Dark Violet - Content Areas
            'button': '#FF69B4',       # Hot Pink - Button Action
            'button_hover': '#9D4EDD', # Deep Purple - Button Hover
            'success': '#00b894',      # Mint - Success Messages
            'warning': '#fab1a0'       # Soft Peach - Warnings
        }
        
        master.configure(bg=self.COLORS['background'])
        
        # Style configuration with Sunset Theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Notebook (Tabs) Styling - Lebih Modern
        self.style.configure('TNotebook', background=self.COLORS['background'], borderwidth=0)
        self.style.configure('TNotebook.Tab', font=('Segoe UI', 12, 'bold'), padding=[25, 12], 
                            background=self.COLORS['card'], foreground=self.COLORS['text_secondary'])
        self.style.map('TNotebook.Tab', 
                      background=[('selected', self.COLORS['button'])], 
                      foreground=[('selected', 'white')])
        
        # Frame Styling
        self.style.configure('TFrame', background=self.COLORS['background'])
        self.style.configure('Card.TFrame', background=self.COLORS['card']) # Container beda warna
        
        # LabelFrame Styling - Lebih Rapi
        self.style.configure('TLabelframe', background=self.COLORS['background'], foreground=self.COLORS['primary'], relief='flat')
        self.style.configure('TLabelframe.Label', background=self.COLORS['background'], foreground=self.COLORS['primary'], font=('Segoe UI', 13, 'bold'))
        
        # Label Styling
        self.style.configure('TLabel', background=self.COLORS['background'], foreground=self.COLORS['text'])
        self.style.configure('Card.TLabel', background=self.COLORS['card'], foreground=self.COLORS['text'])
        
        # Button Styling (Sunscape Premium Buttons)
        self.style.configure('Fun.TButton', font=('Segoe UI', 11, 'bold'), 
                            foreground='white', background=self.COLORS['button'], borderwidth=0, padding=8)
        self.style.map('Fun.TButton', 
                      background=[('active', self.COLORS['button_hover']), ('pressed', self.COLORS['accent'])],
                      foreground=[('active', 'white')])
                      
        # Entry Styling
        self.style.configure('TEntry', fieldbackground=self.COLORS['card'], foreground='white', padding=5) 
        
        # Combobox Styling
        self.style.configure('TCombobox', fieldbackground=self.COLORS['card'], background=self.COLORS['button'], arrowcolor='white')
        
        # Scrollbar - Thin & Modern
        self.style.configure('Vertical.TScrollbar', background=self.COLORS['card'], troughcolor=self.COLORS['background'], 
                            arrowcolor=self.COLORS['primary'], gripcount=0, relief='flat')
        
        # Data initialization
        self.library = DoublyLinkedList()
        self.user_manager = UserManager()
        self._seed_data()
        self.current_user = self.user_manager.users["U001"] 
        self.current_playlist_name = "My Playlist"
        self.current_playlist: Optional[Playlist] = self.current_user.playlists.get(self.current_playlist_name)
        self.player_stack = PlayerStack()
        self.smart_queue = SmartQueue()
        self.current_playing_song: Optional[Song] = None
        self.is_playing = False
        self.playback_context = "playlist"  # "playlist" atau "library"
        self.shuffle_enabled = False
        self.repeat_mode = "none"
        self.shuffled_order: Optional[list[str]] = None
        self.original_order: Optional[list[str]] = None
        self.current_index_in_shuffle: int = -1
        self.current_library_index: int = -1  # Track index di library untuk mode library
        
        # Statistics - FIX: tambah total_play_time
        self.songs_played = []
        self.total_play_time = 0  # dalam detik
        
        # Floating player
        self.floating_player = FloatingPlayerWindow(master, self)
        
        # Main frame
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
        self._update_queue_listbox()

    def _seed_data(self):
        """Inisialisasi data dummy"""
        self.library.add_song("Garis Waktu", "Fiersa Besari", "Pop Akustik", "2016", "3:50")
        self.library.add_song("Sempurna", "Andra and The Backbone", "Rock Pop", "2007", "4:30")
        self.library.add_song("Hujan Di Bulan Juni", "Efek Rumah Kaca", "Indie Pop", "2007", "4:00")
        self.library.add_song("Pelangi", "HIVI!", "Pop", "2012", "3:35")
        self.library.add_song("Dunia Fantasi", "J-Rocks", "Japanese Rock", "2007", "3:40")
        self.library.add_song("Di Atas Awan", "Nidji", "Pop Rock", "2006", "4:15")
        self.library.add_song("Pop Akustik Lagu Baru", "Fiersa Besari", "Pop Akustik", "2023", "3:20")
        
        # Default user dengan hanya 2 playlist
        default_user = self.user_manager.add_user("Zalsa")
        self.user_manager.add_playlist(default_user.id, "My Playlist")
        self.user_manager.add_playlist(default_user.id, "Favorites")
        
        playlist = default_user.playlists["My Playlist"]
        playlist.add_song("S0001") 
        playlist.add_song("S0003") 
        playlist.add_song("S0006")

    def _format_library_list(self, songs: list[Song]) -> tuple[str, ...]:
        """Format daftar lagu untuk ditampilkan di listbox"""
        if not songs: 
            return ("--- Library Kosong ---",)
        max_id = max(len(s.id) for s in songs) if songs else 4
        max_title = max(len(s.title) for s in songs) if songs else 15
        max_artist = max(len(s.artist) for s in songs) if songs else 15
        max_genre = max(len(s.genre) for s in songs) if songs else 10
        max_year = 4
        max_duration = max(len(s.duration) for s in songs) if songs else 5
        formatted = []
        for s in songs:
            line = f"{s.id.ljust(max_id)} | {s.title.ljust(max_title)} | {s.artist.ljust(max_artist)} | {s.genre.ljust(max_genre)} | {s.year.ljust(max_year)} | {s.duration.ljust(max_duration)}"
            formatted.append(line)
        return tuple(formatted)

    def _update_listbox(self):
        """Update library listbox"""
        songs = self.library.get_all_songs()
        formatted_songs = self._format_library_list(songs)
        self.library_listbox.delete(0, tk.END)
        for song_line in formatted_songs:
            self.library_listbox.insert(tk.END, song_line)

    # ============= TAB 1: HOME UI (USER DASHBOARD) =============
    def _setup_home_ui(self, frame):
        """Setup HOME tab dengan user dashboard"""
        # Header with Gradient Text feel (Primary Color)
        header_frame = ttk.Frame(frame, padding="25 25 25 10", style='TFrame')
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="🌅 SUNSCAPE", font=("Segoe UI", 28, "bold"), foreground=self.COLORS['primary']).pack(anchor='w')
        ttk.Label(header_frame, text="Lanskap Musik dalam Cahaya Senja", font=("Segoe UI", 14, "italic"), foreground=self.COLORS['accent']).pack(anchor='w')
        
        # User Profile Section - Clean Layout
        profile_frame = ttk.LabelFrame(frame, text="👤  P R O F I L", padding="20", style='TLabelframe')
        profile_frame.pack(fill="x", pady=15, padx=25)
        
        ttk.Label(profile_frame, text=f"{self.current_user.username}", font=("Segoe UI", 24, "bold"), foreground='white').pack(anchor='w', pady=(0,5))
        ttk.Label(profile_frame, text=f"ID: {self.current_user.id}  •  Member Since: {datetime.now().strftime('%B %Y')}", 
                 font=("Segoe UI", 11), foreground=self.COLORS['text_secondary']).pack(anchor='w')
        
        # Statistics Section
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
        self.most_artist_label.pack(anchor='w', pady=(0, 15))
        
        # Quick Actions
        actions_frame = ttk.LabelFrame(frame, text="⚡ Quick Actions", padding="15", style='TLabelframe')
        actions_frame.pack(fill="x", pady=10, padx=20)
        
        action_buttons = ttk.Frame(actions_frame, style='TFrame')
        action_buttons.pack(fill="x", pady=10)
        
        ttk.Button(action_buttons, text="🎵 Play Random Song", command=self._play_random_song, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(action_buttons, text="⭐ Go to Playlists", command=lambda: self.notebook.select(3), style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(action_buttons, text="🔍 Search Songs", command=lambda: self.notebook.select(2), style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=5)
        
        # Recent Activity
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
        self.recent_listbox.config(yscrollcommand=scroll.set)
        # ============= TAB 2: ADMIN UI =============
    def _setup_admin_ui(self, frame):
        """Setup ADMIN tab untuk library control"""
        header_frame = ttk.Frame(frame, padding="15 15 15 5", style='TFrame')
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="🔑 Control Panel Admin", font=("Segoe UI", 18, "bold"), foreground=self.COLORS['primary']).pack(anchor='w')
        ttk.Label(header_frame, text="Kelola Master Data Lagu. Semua perubahan sinkron otomatis ke User.", font=("Segoe UI", 10, "italic"), foreground=self.COLORS['text_secondary']).pack(anchor='w')
        
        action_frame = ttk.Frame(frame, padding="10 0", style='TFrame')
        action_frame.pack(fill="x", pady=10)
        ttk.Button(action_frame, text="➕ Tambah Lagu Baru", command=self.open_add_dialog, style='Fun.TButton').pack(side="left", padx=10)
        ttk.Button(action_frame, text="✏️ Edit Data Lagu", command=self.open_edit_dialog, style='Fun.TButton').pack(side="left", padx=10)
        ttk.Button(action_frame, text="❌ Hapus Lagu", command=self.delete_song_action, style='Fun.TButton').pack(side="left", padx=10)
        
        list_header_frame = ttk.Frame(frame, padding="10 5 10 0", style='TFrame')
        list_header_frame.pack(fill="x")
        ttk.Label(list_header_frame, text="ID | Judul | Penyanyi | Genre | Tahun | Durasi", font=("Courier", 10, "bold"), foreground=self.COLORS['accent']).pack(anchor="w")
        
        listbox_frame = ttk.Frame(frame, padding="10 5", style='TFrame')
        listbox_frame.pack(fill="both", expand=True)
        self.library_listbox = tk.Listbox(listbox_frame, height=15, font=("Courier", 10), bd=0, highlightthickness=0, 
                                          selectbackground=self.COLORS['button'], selectforeground='white',
                                          bg=self.COLORS['card'], fg='white')
        self.library_listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.library_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.library_listbox.config(yscrollcommand=scrollbar.set)

    # ============= TAB 3: CARI & ANTRIAN UI =============
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
        ttk.Button(queue_frame, text="💾 Save as Playlist", command=self._save_queue_as_playlist, style='Fun.TButton').pack(fill="x", pady=3)

    # ============= TAB 4: PLAYLIST UI =============
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
        ToolTip(delete_btn, "Menghapus SELURUH playlist yang dipilih (bukan hanya lagu)")

    # ============= PLAYER METHODS =============
    def _play_random_song(self):
        """Play lagu random dari library"""
        all_songs = self.library.get_all_songs()
        if not all_songs:
            messagebox.showwarning("Peringatan", "Library kosong!")
            return
        
        song = random.choice(all_songs)
        self._start_playing_song(song, "library")

    def _start_playing_song(self, song: Song, context: str):
        """Helper method untuk memulai playback dengan tracking statistik"""
        # FIX BUG: Pastikan timer lama mati sebelum mulai baru
        self.floating_player.stop_timer()
        
        self.current_playing_song = song
        self.is_playing = True
        self.playback_context = context
        
        # FIX BUG #5: Track play time
        duration_sec = self._parse_duration_to_seconds(song.duration)
        self.total_play_time += duration_sec
        
        # Update statistics
        self._update_statistics(song)
        
        # Show player
        self._show_floating_player()
        self.floating_player.update_display(song, True)
        self.floating_player.start_timer()
    
    def _parse_duration_to_seconds(self, duration: str) -> int:
        """Parse duration string ke detik"""
        try:
            parts = duration.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            return 0
        except:
            return 0

    def _show_floating_player(self):
        """Tampilkan floating player window"""
        self.floating_player.create_window()

    def _update_statistics(self, song: Song):
        """Update statistik user"""
        if song not in self.songs_played:
            self.songs_played.append(song)
        
        # Update recent activity
        self.recent_listbox.insert(0, f"► {song.title} - {song.artist}")
        if self.recent_listbox.size() > 10:
            self.recent_listbox.delete(10, tk.END)
        
        # Update statistics display
        self.total_songs_label.config(text=str(len(self.songs_played)))
        
        # FIX BUG #5: Update total minutes
        total_minutes = int(self.total_play_time / 60)
        self.total_minutes_label.config(text=f"{total_minutes} min")
        
        # Calculate favorite genre
        if self.songs_played:
            genres = [s.genre for s in self.songs_played]
            fav_genre = max(set(genres), key=genres.count)
            self.fav_genre_label.config(text=fav_genre)
        
        # Calculate most played artist
        if self.songs_played:
            artists = [s.artist for s in self.songs_played]
            most_artist = max(set(artists), key=artists.count)
            self.most_artist_label.config(text=most_artist)

    # ============= ADMIN METHODS =============
    def _create_dialog_window(self, title):
        """Buat dialog window"""
        dialog = tk.Toplevel(self.master)
        dialog.title(title)
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()
        return dialog

    def open_add_dialog(self):
        """Dialog untuk tambah lagu"""
        dialog = self._create_dialog_window("Tambah Lagu")
        input_frame = ttk.Frame(dialog, padding="20")
        input_frame.pack(fill="both", expand=True)
        
        title_var = tk.StringVar()
        artist_var = tk.StringVar()
        genre_var = tk.StringVar()
        year_var = tk.StringVar()
        duration_var = tk.StringVar()
        
        ttk.Label(input_frame, text="Judul Lagu:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=title_var, width=30).grid(row=0, column=1, pady=5, padx=5)
        ttk.Label(input_frame, text="Penyanyi:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=artist_var, width=30).grid(row=1, column=1, pady=5, padx=5)
        ttk.Label(input_frame, text="Genre:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=genre_var, width=30).grid(row=2, column=1, pady=5, padx=5)
        ttk.Label(input_frame, text="Tahun Rilis:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=year_var, width=30).grid(row=3, column=1, pady=5, padx=5)
        ttk.Label(input_frame, text="Durasi (contoh: 3:45):").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=duration_var, width=30).grid(row=4, column=1, pady=5, padx=5)
        
        def submit():
            title = title_var.get().strip()
            artist = artist_var.get().strip()
            genre = genre_var.get().strip()
            year = year_var.get().strip()
            duration = duration_var.get().strip()
            
            if not all([title, artist, genre, year, duration]):
                messagebox.showwarning("Peringatan", "Semua field harus diisi!")
                return
                
            # FIX: Auto-normalize duration (e.g., 3:65 -> 4:05)
            # Revert strict regex, allow any digits for seconds as long as format is M:S
            if not re.match(r'^\d+:\d+$', duration):
                 messagebox.showerror("Format Salah", "Format durasi harus MM:SS (Contoh: 04:30).")
                 return
            
            # Normalize logic
            try:
                mins, secs = map(int, duration.split(':'))
                total_secs = mins * 60 + secs
                norm_mins = total_secs // 60
                norm_secs = total_secs % 60
                duration = f"{norm_mins}:{norm_secs:02d}"
            except ValueError:
                 messagebox.showerror("Error", "Durasi tidak valid.")
                 return

            # FIX: Validasi Tahun (1800 - 2025)
            if not (year.isdigit() and 1800 <= int(year) <= 2025):
                messagebox.showerror("Format Salah", "Tahun harus angka antara 1800 - 2025.")
                return

            if self.library.add_song(title, artist, genre, year, duration):
                messagebox.showinfo("Sukses", f"Lagu '{title}' berhasil ditambahkan!")
                self._update_listbox()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Gagal menambahkan lagu.")
        
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill="x")
        ttk.Button(button_frame, text="OK", command=submit, style='Fun.TButton').pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)

    def open_edit_dialog(self):
        """Dialog untuk edit lagu"""
        try:
            selected_line = self.library_listbox.get(self.library_listbox.curselection())
            song_id = selected_line.split(' | ')[0].strip()
        except tk.TclError:
            messagebox.showwarning("Peringatan", "Pilih lagu yang ingin diedit terlebih dahulu.")
            return
        
        old_song = self.library.id_map.get(song_id)
        if not old_song:
            messagebox.showerror("Error", "Lagu tidak ditemukan.")
            return
        
        dialog = self._create_dialog_window("Edit Lagu")
        input_frame = ttk.Frame(dialog, padding="20")
        input_frame.pack(fill="both", expand=True)
        
        title_var = tk.StringVar(value=old_song.title)
        artist_var = tk.StringVar(value=old_song.artist)
        genre_var = tk.StringVar(value=old_song.genre)
        year_var = tk.StringVar(value=old_song.year)
        duration_var = tk.StringVar(value=old_song.duration)
        
        ttk.Label(input_frame, text="Judul Lagu:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=title_var, width=30).grid(row=0, column=1, pady=5, padx=5)
        ttk.Label(input_frame, text="Penyanyi:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=artist_var, width=30).grid(row=1, column=1, pady=5, padx=5)
        ttk.Label(input_frame, text="Genre:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=genre_var, width=30).grid(row=2, column=1, pady=5, padx=5)
        ttk.Label(input_frame, text="Tahun Rilis:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=year_var, width=30).grid(row=3, column=1, pady=5, padx=5)
        ttk.Label(input_frame, text="Durasi:").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=duration_var, width=30).grid(row=4, column=1, pady=5, padx=5)
        
        def submit():
            new_title = title_var.get().strip()
            new_artist = artist_var.get().strip()
            new_genre = genre_var.get().strip()
            new_year = year_var.get().strip()
            new_duration = duration_var.get().strip()
            
            # FIX: Auto-normalize duration (e.g., 3:65 -> 4:05)
            if not re.match(r'^\d+:\d+$', new_duration):
                 messagebox.showerror("Format Salah", "Format durasi harus MM:SS (Contoh: 04:30).")
                 return
            
            try:
                mins, secs = map(int, new_duration.split(':'))
                total_secs = mins * 60 + secs
                norm_mins = total_secs // 60
                norm_secs = total_secs % 60
                new_duration = f"{norm_mins}:{norm_secs:02d}"
            except ValueError:
                 messagebox.showerror("Error", "Durasi tidak valid.")
                 return
                
            # FIX: Validasi Tahun (1800 - 2025)
            if not (new_year.isdigit() and 1800 <= int(new_year) <= 2025):
                messagebox.showerror("Format Salah", "Tahun harus angka antara 1800 - 2025.")
                return
                
            if self.library.edit_song(song_id, new_title, new_artist, new_genre, new_year, new_duration):
                messagebox.showinfo("Sukses", f"Lagu ID {song_id} berhasil diupdate!")
                self._update_listbox()
                self._update_playlist_listbox()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Gagal mengedit lagu.")
        
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill="x")
        ttk.Button(button_frame, text="OK", command=submit, style='Fun.TButton').pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)

    def delete_song_action(self):
        """Hapus lagu dari library"""
        try:
            selected_line = self.library_listbox.get(self.library_listbox.curselection())
            song_id = selected_line.split(' | ')[0].strip()
        except tk.TclError:
            messagebox.showwarning("Peringatan", "Pilih lagu yang ingin dihapus terlebih dahulu.")
            return
        
        if messagebox.askyesno("Konfirmasi Hapus", f"Yakin menghapus lagu ID {song_id}?"):
            if self.library.delete_song(song_id):
                total_removed = 0
                for user in self.user_manager.users.values():
                    for playlist in user.playlists.values():
                        total_removed += playlist.remove_all_references(song_id)
                
                if self.current_playing_song and self.current_playing_song.id == song_id:
                    self.current_playing_song = None
                    self.is_playing = False
                    self.floating_player.stop_timer()
                
                messagebox.showinfo("Sukses", f"Lagu ID {song_id} berhasil dihapus!")
                self._update_listbox()
                self._update_playlist_listbox()
            else:
                messagebox.showerror("Error", "Gagal menghapus lagu.")

    # ============= SEARCH METHODS =============
    def _search_song_action(self, keyword: str, by: str):
        """Cari lagu berdasarkan keyword"""
        if not keyword.strip():
            self.search_listbox.delete(0, tk.END)
            return
        
        keyword = keyword.strip().lower()
        results = []
        current = self.library.head
        while current:
            song = current.data
            match = False
            if by == "id":
                if keyword in song.id.lower():
                    match = True
            elif by == "title":
                dist = levenshtein_distance(keyword, song.title.lower())
                if dist <= 2:
                    match = True
            elif by == "artist":
                dist = levenshtein_distance(keyword, song.artist.lower())
                if dist <= 2:
                    match = True
            if match:
                results.append(song)
            current = current.next
        
        self.search_listbox.delete(0, tk.END)
        if results:
            formatted_results = self._format_library_list(results)
            for line in formatted_results:
                self.search_listbox.insert(tk.END, line)
        else:
            self.search_listbox.insert(tk.END, "Tidak ditemukan lagu.")

    # FIX BUG #3: Tambah lagu dari search ke playlist - VALIDASI & VERIFIKASI
    def _add_to_selected_playlist_from_search(self):
        """Tambah lagu dari search ke playlist"""
        try:
            selected_index = self.search_listbox.curselection()[0]
            selected_line = self.search_listbox.get(selected_index)
            
            # Validasi: jika hasil "Tidak ditemukan lagu."
            if "Tidak ditemukan" in selected_line or "kosong" in selected_line.lower():
                messagebox.showwarning("Peringatan", "Pilih lagu yang valid!")
                return
            
            song_id = selected_line.split(' | ')[0].strip()
        except (IndexError, tk.TclError):
            messagebox.showwarning("Peringatan", "Pilih lagu dari hasil pencarian dulu!")
            return
        
        target_name = self.target_playlist_var.get()
        target_playlist = self.current_user.playlists.get(target_name)
        if not target_playlist:
            messagebox.showerror("Error", f"Playlist '{target_name}' tidak ditemukan!")
            return
        
        # TAMBAH KE PLAYLIST
        if target_playlist.add_song(song_id):
            # VERIFIKASI: cek apakah benar ditambahkan
            if song_id in target_playlist.to_list():
                song = self.library.id_map.get(song_id)
                title = song.title if song else song_id
                messagebox.showinfo("✅ Sukses!", f"'{title}' berhasil ditambahkan ke playlist '{target_name}'!")
                
                # Jika playlist yang ditampilkan adalah target, refresh
                if self.current_playlist_name == target_name:
                    self._update_playlist_listbox()
            else:
                messagebox.showerror("Error", "Lagu gagal ditambahkan ke playlist!")
        else:
            messagebox.showinfo("ℹ️", f"Lagu ini sudah ada di playlist '{target_name}'.")

    # FIX BUG #1: Play dari library - urutan library saja, TANPA logika similar
    def _play_from_library(self):
        """Play lagu dari search results - urut library"""
        try:
            selected = self.search_listbox.get(self.search_listbox.curselection())
            song_id = selected.split(' | ')[0].strip()
            song = self.library.id_map.get(song_id)
            if song:
                # Set index di library
                all_songs = self.library.get_all_songs()
                try:
                    self.current_library_index = next(i for i, s in enumerate(all_songs) if s.id == song_id)
                except StopIteration:
                    self.current_library_index = 0
                
                self._start_playing_song(song, "library")
            else:
                messagebox.showerror("Error", "Lagu tidak ditemukan di library.")
        except tk.TclError:
            messagebox.showwarning("Peringatan", "Pilih lagu dari hasil pencarian dulu!")

    def _like_from_search(self):
        """Tambah ke favorites dari search"""
        try:
            selected = self.search_listbox.get(self.search_listbox.curselection())
            song_id = selected.split(' | ')[0].strip()
        except tk.TclError:
            messagebox.showwarning("Peringatan", "Pilih lagu dari hasil pencarian dulu!")
            return
        self._add_to_favorites(song_id)

    # FIX BUG #2: Like dari playlist - HANYA satu lagu!
    def _like_from_playlist(self):
        """Tambah ke favorites dari playlist - SATU LAGU SAJA"""
        try:
            selected_index = self.playlist_listbox.curselection()[0]  # Ambil index pertama
            selected_line = self.playlist_listbox.get(selected_index)
            song_id = selected_line.split(' | ')[0].strip()
            
            # Tambah HANYA lagu ini ke favorites
            self._add_to_favorites(song_id)
        except IndexError:
            messagebox.showwarning("Peringatan", "Pilih SATU lagu dari playlist!")
        except tk.TclError:
            messagebox.showwarning("Peringatan", "Pilih lagu dari playlist dulu!")

    def _add_to_favorites(self, song_id: str):
        """Tambah lagu ke favorites"""
        favorites = self.current_user.playlists.get("Favorites")
        if not favorites:
            messagebox.showerror("Error", "Playlist Favorites tidak ditemukan!")
            return
        
        if favorites.add_song(song_id):
            song = self.library.id_map.get(song_id)
            title = song.title if song else song_id
            messagebox.showinfo("❤️ Berhasil!", f"'{title}' telah ditambahkan ke Favorites!")
            if self.current_playlist_name == "Favorites":
                self._update_playlist_listbox()
        else:
            messagebox.showinfo("ℹ️", "Lagu ini sudah ada di Favorites!")

    # ============= QUEUE METHODS =============
    # FIX BUG #5: Play dari queue dengan popup player
    def _play_from_queue(self):
        """Play lagu pertama dari queue"""
        if not self.smart_queue.queue:
            messagebox.showwarning("Peringatan", "Antrian kosong!")
            return
        
        # Ambil lagu pertama
        song = self.smart_queue.queue[0]
        
        # HAPUS dari queue SETELAH diambil
        self.smart_queue.queue.pop(0)
        self._update_queue_listbox()
        
        # PUTAR dengan popup player (menggunakan helper method)
        self._start_playing_song(song, "queue")
    
    def _add_to_queue_next(self):
        """Tambah ke queue - mainkan pertama kali"""
        song = self._get_selected_song_from_search_or_playlist()
        if song:
            self.smart_queue.add_next(song)
            self._update_queue_listbox()

    def _add_to_queue_later(self):
        """Tambah ke queue - mainkan terakhir kali"""
        song = self._get_selected_song_from_search_or_playlist()
        if song:
            self.smart_queue.add_later(song)
            self._update_queue_listbox()

    def _get_selected_song_from_search_or_playlist(self) -> Optional[Song]:
        """Ambil lagu yang dipilih dari search atau playlist"""
        try:
            selected = self.search_listbox.get(self.search_listbox.curselection())
            song_id = selected.split(' | ')[0].strip()
        except tk.TclError:
            try:
                selected = self.playlist_listbox.get(self.playlist_listbox.curselection())
                song_id = selected.split(' | ')[0].strip()
            except tk.TclError:
                messagebox.showwarning("Peringatan", "Pilih lagu dari hasil pencarian atau playlist.")
                return None
        return self.library.id_map.get(song_id)

    def _update_queue_listbox(self):
        """Update queue listbox"""
        self.queue_listbox.delete(0, tk.END)
        queue_songs = self.smart_queue.to_list()
        if not queue_songs:
            self.queue_listbox.insert(tk.END, "Antrian kosong.")
        else:
            formatted = self._format_library_list(queue_songs)
            for line in formatted:
                self.queue_listbox.insert(tk.END, line)

    def _clear_queue(self):
        """Kosongkan queue"""
        self.smart_queue.clear()
        self._update_queue_listbox()

    # FIX BUG #4: Save queue as playlist - NO DUPLICATE!
    def _save_queue_as_playlist(self):
        """Simpan queue sebagai playlist baru"""
        queue_songs = self.smart_queue.to_list()
        if not queue_songs:
            messagebox.showwarning("Peringatan", "Antrian kosong!")
            return
        
        dialog = tk.Toplevel(self.master)
        dialog.title("Simpan Queue sebagai Playlist")
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.configure(bg=self.COLORS['card'])
        
        tk.Label(dialog, text="Nama Playlist Baru:", bg=self.COLORS['card'], 
                font=("Segoe UI", 11, "bold")).pack(pady=15)
        name_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=name_var, width=30, font=("Segoe UI", 11))
        entry.pack(pady=5, padx=20)
        entry.focus()
        
        def save():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Peringatan", "Nama playlist tidak boleh kosong!")
                return
            if name in self.current_user.playlists:
                messagebox.showwarning("Peringatan", f"Playlist '{name}' sudah ada!")
                return
            
            # BUAT PLAYLIST BARU - KOSONG DULU
            if self.user_manager.add_playlist(self.current_user.id, name):
                new_playlist = self.current_user.playlists[name]
                
                # TAMBAH SATU-SATU LAGU DARI QUEUE (bukan dari playlist lain!)
                for song in queue_songs:  # queue_songs adalah list[Song]
                    new_playlist.add_song(song.id)  # Tambah ID lagu dari queue
                
                # VERIFIKASI: playlist baru HARUS sama dengan queue
                new_playlist_ids = new_playlist.to_list()
                queue_ids = [s.id for s in queue_songs]
                
                if new_playlist_ids == queue_ids:
                    messagebox.showinfo("Sukses", f"Antrian disimpan sebagai playlist '{name}'!\nTotal {len(queue_songs)} lagu.")
                    self._clear_queue()
                    
                    # Update dropdown
                    playlist_names = list(self.current_user.playlists.keys())
                    self.active_playlist_dropdown['values'] = playlist_names
                    self.playlist_dropdown['values'] = playlist_names
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", f"Gagal menyimpan queue! Expected {len(queue_ids)} lagu, got {len(new_playlist_ids)}.")
            else:
                messagebox.showerror("Error", "Gagal membuat playlist.")
        
        btn_frame = tk.Frame(dialog, bg=self.COLORS['card'])
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="Simpan", command=save, bg=self.COLORS['button'], 
                 fg="white", font=("Segoe UI", 10, "bold"), padx=20, pady=5, 
                 relief="flat", cursor="hand2").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Batal", command=dialog.destroy, bg="#808080", 
                 fg="white", font=("Segoe UI", 10, "bold"), padx=20, pady=5, 
                 relief="flat", cursor="hand2").pack(side="left", padx=5)

    # ============= PLAYLIST METHODS =============
    def _switch_playlist(self, event=None):
        """Beralih ke playlist lain"""
        new_name = self.active_playlist_var.get()
        if new_name in self.current_user.playlists:
            self.current_playlist_name = new_name
            self.current_playlist = self.current_user.playlists[new_name]
            self._update_playlist_listbox()

    def _move_song_up(self):
        """Pindah lagu ke atas"""
        try:
            selected_line = self.playlist_listbox.get(self.playlist_listbox.curselection())
            song_id = selected_line.split(' | ')[0].strip()
            if self.current_playlist.move_song_up(song_id):
                self._update_playlist_listbox()
                self.current_playlist.current_play = None
        except tk.TclError:
            pass

    def _move_song_down(self):
        """Pindah lagu ke bawah"""
        try:
            selected_line = self.playlist_listbox.get(self.playlist_listbox.curselection())
            song_id = selected_line.split(' | ')[0].strip()
            if self.current_playlist.move_song_down(song_id):
                self._update_playlist_listbox()
                self.current_playlist.current_play = None
        except tk.TclError:
            pass

    def _play_selected_from_playlist(self):
        """Play lagu yang dipilih dari playlist"""
        try:
            selected_line = self.playlist_listbox.get(self.playlist_listbox.curselection())
            song_id = selected_line.split(' | ')[0].strip()
            target_song = self.library.id_map.get(song_id)
            if target_song:
                # Set context ke playlist
                if self.shuffle_enabled and self.shuffled_order:
                    try:
                        self.current_index_in_shuffle = self.shuffled_order.index(song_id)
                    except ValueError:
                        self.current_index_in_shuffle = 0
                else:
                    self.current_playlist.current_play = None
                
                self._start_playing_song(target_song, "playlist")
        except tk.TclError:
            messagebox.showwarning("Peringatan", "Pilih lagu dari Playlist.")

    # FIX BUG #1: Remove dari playlist - HAPUS SATU LAGU SAJA!
    def _remove_from_playlist(self):
        """Hapus lagu dari playlist - SATU LAGU SAJA"""
        try:
            selected_index = self.playlist_listbox.curselection()[0]  # Ambil index
            selected_line = self.playlist_listbox.get(selected_index)
            
            # Validasi: jika playlist kosong
            if "kosong" in selected_line.lower():
                messagebox.showwarning("Peringatan", "Playlist kosong!")
                return
            
            song_id = selected_line.split(' | ')[0].strip()
            
            # Konfirmasi
            song = self.library.id_map.get(song_id)
            song_title = song.title if song else song_id
            
            if not messagebox.askyesno("Konfirmasi", f"Hapus '{song_title}' dari playlist '{self.current_playlist_name}'?"):
                return
            
            # HAPUS HANYA LAGU INI dari playlist
            if self.current_playlist and self.current_playlist.remove_song_by_id(song_id):
                messagebox.showinfo("Sukses", f"'{song_title}' berhasil dihapus dari playlist '{self.current_playlist_name}'.")
                
                # Update listbox - refresh semua
                self._update_playlist_listbox()
                
                # Jika lagu yg dihapus sedang diputar, stop
                if self.current_playing_song and self.current_playing_song.id == song_id:
                    self.current_playing_song = None
                    self.is_playing = False
                    self.floating_player.stop_timer()
            else:
                messagebox.showerror("Error", "Gagal menghapus lagu dari playlist.")
                
        except IndexError:
            messagebox.showwarning("Peringatan", "Pilih lagu yang ingin dihapus dari playlist!")
        except tk.TclError:
            messagebox.showwarning("Peringatan", "Pilih lagu yang ingin dihapus dari playlist!")

    def _delete_current_playlist(self):
        """Hapus playlist saat ini"""
        name = self.current_playlist_name
        if name == "My Playlist" or name == "Favorites":
             messagebox.showwarning("Peringatan", "Playlist default tidak bisa dihapus!")
             return
             
        if messagebox.askyesno("Konfirmasi", f"Yakin menghapus playlist '{name}'?"):
            if self.user_manager.remove_playlist(self.current_user.id, name):
                messagebox.showinfo("Sukses", "Playlist dihapus.")
                # Reset ke default
                self.current_playlist_name = "My Playlist"
                self.current_playlist = self.current_user.playlists.get("My Playlist")
                self.active_playlist_var.set("My Playlist")
                
                # Update dropdowns
                names = list(self.current_user.playlists.keys())
                self.active_playlist_dropdown['values'] = names
                self.playlist_dropdown['values'] = names
                
                self._update_playlist_listbox()
            else:
                messagebox.showerror("Error", "Gagal menghapus playlist.")

    def _sort_playlist_by_id(self):
        """Sort lagu di playlist berdasarkan ID"""
        if not self.current_playlist or not self.current_playlist.head:
            return
            
        # Matikan shuffle jika aktif
        if self.shuffle_enabled:
            self.shuffle_enabled = False
            self.shuffled_order = None
            self.current_index_in_shuffle = -1
            try:
                self.btn_shuffle.config(text="🔀 Shuffle: OFF")
            except:
                pass
        
        # Ambil semua lagu, sort by ID, lalu rebuild playlist
        current_ids = self.current_playlist.to_list()
        sorted_ids = sorted(current_ids)
        
        # Reset playlist
        self.current_playlist.head = None
        self.current_playlist.tail = None
        self.current_playlist.size = 0
        
        for pid in sorted_ids:
            self.current_playlist.add_song(pid)
            
        self._update_playlist_listbox()
        messagebox.showinfo("Info", "Playlist diurutkan berdasarkan ID.")

    def _update_playlist_listbox(self):
        """Update playlist listbox"""
        self.playlist_listbox.delete(0, tk.END)
        if not self.current_playlist or not self.current_playlist.head:
            self.playlist_listbox.insert(tk.END, "Playlist kosong.")
            return
        
        if self.shuffle_enabled and self.shuffled_order:
            display_ids = self.shuffled_order
        else:
            display_ids = self.current_playlist.to_list()
        
        playlist_songs = []
        for song_id in display_ids:
            song = self.library.id_map.get(song_id)
            if song:
                playlist_songs.append(song)
        
        formatted_list = self._format_library_list(playlist_songs)
        for line in formatted_list:
            self.playlist_listbox.insert(tk.END, line)

    # ============= PLAYER CONTROLS =============
    def _toggle_play_stop(self):
        """Toggle play/stop"""
        if self.is_playing:
            self.is_playing = False
            self.floating_player.update_display(self.current_playing_song, False)
            self.floating_player.stop_timer()
        else:
            if not self.current_playing_song and self.current_playlist and self.current_playlist.head:
                first_song_id = self.current_playlist.head.song_id
                self.current_playing_song = self.library.id_map.get(first_song_id)
                self.playback_context = "playlist"
                if self.shuffle_enabled:
                    self.current_index_in_shuffle = 0
                self.current_playlist.current_play = None
            
            if self.current_playing_song:
                self.is_playing = True
                self._show_floating_player()
                self.floating_player.update_display(self.current_playing_song, True)
                self.floating_player.start_timer()
            else:
                messagebox.showwarning("Peringatan", "Tidak ada lagu yang dipilih.")

    def _toggle_shuffle(self):
        """Toggle shuffle mode - HANYA untuk playlist"""
        if self.playback_context != "playlist":
            messagebox.showwarning("Peringatan", "Shuffle hanya tersedia di mode Playlist!")
            return
        
        if not self.current_playlist or not self.current_playlist.head:
            messagebox.showwarning("Peringatan", "Playlist kosong!")
            return
        
        self.shuffle_enabled = not self.shuffle_enabled
        
        if self.shuffle_enabled:
            # FIX: Update Button Text
            try: self.btn_shuffle.config(text="🔀 Shuffle: ON")
            except: pass
            
            self.original_order = self.current_playlist.to_list()
            self.shuffled_order = fisher_yates_shuffle(self.original_order)
            self.current_index_in_shuffle = 0
            self.current_playlist.current_play = None
        else:
            # FIX: Update Button Text
            try: self.btn_shuffle.config(text="🔀 Shuffle: OFF")
            except: pass
            
            self.shuffled_order = None
            self.current_index_in_shuffle = -1
            self.current_playlist.current_play = None
        
        self._update_playlist_listbox()
        self.floating_player.update_display(self.current_playing_song, self.is_playing)

    def _cycle_repeat(self):
        """Cycle repeat mode - HANYA untuk playlist"""
        if self.playback_context != "playlist":
            messagebox.showwarning("Peringatan", "Repeat hanya tersedia di mode Playlist!")
            return
        
        self.repeat_mode = "playlist" if self.repeat_mode == "none" else "none"
        
        # FIX: Update Button Text
        text = f"🔁 Repeat: {self.repeat_mode.upper()}" if self.repeat_mode != "none" else "🔁 Repeat: OFF"
        try: self.btn_repeat.config(text=text)
        except: pass
        
        self.floating_player.update_display(self.current_playing_song, self.is_playing)

    # FIX BUG #1 & #4: NEXT SONG dengan logika yang jelas
    def _next_song(self):
        """NEXT SONG - Logika berdasarkan context"""
        # PRIORITAS 1: Cek queue dulu
        next_from_queue = self.smart_queue.pop_next()
        if next_from_queue:
            self._start_playing_song(next_from_queue, "queue")
            self._update_queue_listbox()
            return
        
        # PRIORITAS 2: Jika dari PLAYLIST
        if self.playback_context == "playlist":
            self._next_song_from_playlist()
            return
        
        # PRIORITAS 3: Jika dari LIBRARY (urutan library)
        if self.playback_context == "library":
            self._next_song_from_library()
            return
    
    def _next_song_from_playlist(self):
        """Next song dalam mode playlist"""
        if self.shuffle_enabled and self.shuffled_order:
            # Mode shuffle
            if self.current_index_in_shuffle == -1 and self.current_playing_song:
                try:
                    self.current_index_in_shuffle = self.shuffled_order.index(self.current_playing_song.id)
                except ValueError:
                    self.current_index_in_shuffle = 0
            
            next_idx = self.current_index_in_shuffle + 1
            if next_idx < len(self.shuffled_order):
                next_id = self.shuffled_order[next_idx]
                next_song = self.library.id_map.get(next_id)
                if next_song:
                    self.current_index_in_shuffle = next_idx
                    self._start_playing_song(next_song, "playlist")
            else:
                # Sudah di akhir
                if self.repeat_mode == "playlist":
                    # Repeat: shuffle ulang dan mulai dari awal
                    self.shuffled_order = fisher_yates_shuffle(self.original_order)
                    next_id = self.shuffled_order[0]
                    next_song = self.library.id_map.get(next_id)
                    if next_song:
                        self.current_index_in_shuffle = 0
                        self._start_playing_song(next_song, "playlist")
                else:
                    # Stop
                    self.is_playing = False
                    self.floating_player.stop_timer()
        else:
            # Mode normal (tanpa shuffle)
            if self.current_playlist and self.current_playlist.current_play:
                next_node = self.current_playlist.current_play.next
                if next_node:
                    next_song = self.library.id_map.get(next_node.song_id)
                    if next_song:
                        self.current_playlist.current_play = next_node
                        self._start_playing_song(next_song, "playlist")
                        return
            
            # Jika tidak ada next atau belum ada current_play, coba dari awal
            if self.current_playlist and self.current_playlist.head:
                if self.repeat_mode == "playlist":
                    first_song = self.library.id_map.get(self.current_playlist.head.song_id)
                    if first_song:
                        self.current_playlist.current_play = self.current_playlist.head
                        self._start_playing_song(first_song, "playlist")
                else:
                    self.is_playing = False
                    self.floating_player.stop_timer()
    
    def _next_song_from_library(self):
        """Next song dalam mode library - Cari LAGU MIRIP"""
        # Requirement: "Next/prev akan memutar lagu yang mirip"
        self._play_similar_song()

    def _play_similar_song(self):
        """Play lagu yang mirip dengan lagu sekarang"""
        if not self.current_playing_song:
            self._play_random_song()
            return

        all_songs = self.library.get_all_songs()
        # Filter lagu selain lagu sekarang
        candidates = [s for s in all_songs if s.id != self.current_playing_song.id]
        
        if not candidates:
            messagebox.showinfo("Info", "Tidak ada lagu lain di library.")
            return

        # Prioritas 1: Artis Sama (Case Insensitive)
        same_artist = [s for s in candidates if s.artist.lower().strip() == self.current_playing_song.artist.lower().strip()]
        if same_artist:
            next_song = random.choice(same_artist)
            print(f"DEBUG: Playing similar artist: {next_song.artist}")
            self._start_playing_song(next_song, "library")
            return

        # Prioritas 2: Genre Sama (Case Insensitive)
        same_genre = [s for s in candidates if s.genre.lower().strip() == self.current_playing_song.genre.lower().strip()]
        if same_genre:
            next_song = random.choice(same_genre)
            print(f"DEBUG: Playing similar genre: {next_song.genre}")
            self._start_playing_song(next_song, "library")
            return
            
        # Fallback: Random
        next_song = random.choice(candidates)
        # messagebox.showinfo("Info", "Tidak ada lagu mirip ditemukan, memutar lagu acak.")
        self._start_playing_song(next_song, "library")

    def _prev_song(self):
        """Previous song"""
        if not self.current_playing_song:
            return
        
        if self.playback_context == "playlist":
            self._prev_song_from_playlist()
        elif self.playback_context == "library":
            self._prev_song_from_library()
    
    def _prev_song_from_playlist(self):
        """Previous song dalam mode playlist"""
        if self.shuffle_enabled and self.shuffled_order:
            if self.current_index_in_shuffle <= 0:
                return
            prev_idx = self.current_index_in_shuffle - 1
            prev_id = self.shuffled_order[prev_idx]
            prev_song = self.library.id_map.get(prev_id)
            if prev_song:
                self.current_index_in_shuffle = prev_idx
                self._start_playing_song(prev_song, "playlist")
        else:
            if self.current_playlist and self.current_playlist.current_play:
                current = self.current_playlist.head
                prev_node = None
                while current and current != self.current_playlist.current_play:
                    if current.next == self.current_playlist.current_play:
                        prev_node = current
                        break
                    current = current.next
                
                if prev_node:
                    prev_song = self.library.id_map.get(prev_node.song_id)
                    if prev_song:
                        self.current_playlist.current_play = prev_node
                        self._start_playing_song(prev_song, "playlist")
    
    def _prev_song_from_library(self):
        """Previous song dalam mode library - Cari LAGU MIRIP (Sama dengan Next)"""
        # Requirement: "Next/prev akan memutar lagu yang mirip"
        self._play_similar_song()


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayerApp(root)
    root.mainloop()