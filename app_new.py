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
        self.window.configure(bg=self.app.COLORS['background'])
        
        # Title
        self.song_title = tk.Label(self.window, text="Memilih Lagu...", font=("Segoe UI", 16, "bold"), 
                                    foreground=self.app.COLORS['accent'], bg=self.app.COLORS['background'], 
                                    wraplength=350, justify="center")
        self.song_title.pack(fill="x", padx=20, pady=(20, 5))
        
        self.song_artist = tk.Label(self.window, text="", font=("Segoe UI", 12), 
                                     foreground=self.app.COLORS['text'], bg=self.app.COLORS['background'], wraplength=350)
        self.song_artist.pack(fill="x", padx=20, pady=(0, 20))
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.window, variable=self.progress_var, 
                                             maximum=100, length=360, mode='determinate')
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        
        # Time display
        self.time_label = tk.Label(self.window, text="0:00 / 0:00", font=("Segoe UI", 11, "bold"), 
                                    foreground=self.app.COLORS['primary'], bg=self.app.COLORS['background'])
        self.time_label.pack(pady=(0, 20))
        
        # Control buttons (Icon-only dengan Tooltips)
        control_frame = tk.Frame(self.window, bg=self.app.COLORS['background'])
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
        self.stop_timer()
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
                    self.app._next_song()
                    return
        
        self.timer_id = self.window.after(1000, self._update_timer)
    
    def stop_timer(self):
        """Stop timer"""
        if self.timer_id:
            self.window.after_cancel(self.timer_id)
            self.timer_id = None


class MusicPlayerApp:
    def __init__(self, master):
        self.master = master
        master.title("🌅 SUNSCAPE")
        master.geometry("1100x800")
        
        # THEME: SUNSCAPE (Sunset Gradient Premium)
        self.COLORS = {
            'primary': '#FF6B35',      # Sunset Orange
            'secondary': '#9D4EDD',    # Deep Purple
            'accent': '#FF69B4',       # Hot Pink
            'background': '#1A0B2E',   # Deep Indigo
            'text': '#FFFFFF',
            'text_secondary': '#D1C4E9',
            'card': '#2D1B4E',
            'button': '#FF69B4',
            'button_hover': '#9D4EDD',
            'success': '#00b894',
            'warning': '#fab1a0'
        }
        
        master.configure(bg=self.COLORS['background'])
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Frame Styling
        self.style.configure('TFrame', background=self.COLORS['background'])
        self.style.configure('Card.TFrame', background=self.COLORS['card'])
        
        # Label Styling
        self.style.configure('TLabel', background=self.COLORS['background'], foreground=self.COLORS['text'])
        self.style.configure('Card.TLabel', background=self.COLORS['card'], foreground=self.COLORS['text'])
        
        # Button Styling
        self.style.configure('Fun.TButton', font=('Segoe UI', 11, 'bold'), 
                            foreground='white', background=self.COLORS['button'], borderwidth=0, padding=8)
        self.style.map('Fun.TButton', 
                      background=[('active', self.COLORS['button_hover']), ('pressed', self.COLORS['accent'])],
                      foreground=[('active', 'white')])
        
        # Large Button for Login
        self.style.configure('Large.TButton', font=('Segoe UI', 14, 'bold'), 
                            foreground='white', background=self.COLORS['button'], borderwidth=0, padding=20)
        self.style.map('Large.TButton', 
                      background=[('active', self.COLORS['button_hover'])],
                      foreground=[('active', 'white')])
        
        # Entry Styling
        self.style.configure('TEntry', fieldbackground=self.COLORS['card'], foreground='white', padding=5)
        
        # Combobox Styling
        self.style.configure('TCombobox', fieldbackground=self.COLORS['card'], background=self.COLORS['button'], arrowcolor='white')
        
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
        self.playback_context = "playlist"
        self.shuffle_enabled = False
        self.repeat_mode = "none"
        self.shuffled_order: Optional[list[str]] = None
        self.original_order: Optional[list[str]] = None
        self.current_index_in_shuffle: int = -1
        self.current_library_index: int = -1
        
        # Statistics
        self.songs_played = []
        self.total_play_time = 0
        
        # Floating player
        self.floating_player = FloatingPlayerWindow(master, self)
        
        # Current mode
        self.current_mode = None  # "user" or "admin"
        
        # Main container
        self.main_container = tk.Frame(master, bg=self.COLORS['background'])
        self.main_container.pack(fill="both", expand=True)
        
        # Current screen frame
        self.current_screen = None
        
        # Show login screen
        self.show_login_screen()

    def _seed_data(self):
        """Inisialisasi data dummy"""
        self.library.add_song("Garis Waktu", "Fiersa Besari", "Pop Akustik", "2016", "3:50")
        self.library.add_song("Sempurna", "Andra and The Backbone", "Rock Pop", "2007", "4:30")
        self.library.add_song("Hujan Di Bulan Juni", "Efek Rumah Kaca", "Indie Pop", "2007", "4:00")
        self.library.add_song("Pelangi", "HIVI!", "Pop", "2012", "3:35")
        self.library.add_song("Dunia Fantasi", "J-Rocks", "Japanese Rock", "2007", "3:40")
        self.library.add_song("Di Atas Awan", "Nidji", "Pop Rock", "2006", "4:15")
        self.library.add_song("Pop Akustik Lagu Baru", "Fiersa Besari", "Pop Akustik", "2023", "3:20")
        
        # Default user dengan 2 playlist
        default_user = self.user_manager.add_user("Zalsa")
        self.user_manager.add_playlist(default_user.id, "My Playlist")
        self.user_manager.add_playlist(default_user.id, "Favorites")
        
        playlist = default_user.playlists["My Playlist"]
        playlist.add_song("S0001")
        playlist.add_song("S0003")
        playlist.add_song("S0006")

    # ============= SCREEN MANAGER =============
    def clear_screen(self):
        """Clear current screen"""
        if self.current_screen:
            self.current_screen.destroy()
        self.current_screen = tk.Frame(self.main_container, bg=self.COLORS['background'])
        self.current_screen.pack(fill="both", expand=True)
        return self.current_screen

    def show_login_screen(self):
        """Show login screen"""
        screen = self.clear_screen()
        
        # Center container
        center = tk.Frame(screen, bg=self.COLORS['background'])
        center.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo and tagline
        tk.Label(center, text="🌅 SUNSCAPE", font=("Segoe UI", 48, "bold"), 
                foreground=self.COLORS['primary'], bg=self.COLORS['background']).pack(pady=(0, 10))
        
        tk.Label(center, text="Musik, senja, dan kamu.", font=("Segoe UI", 16, "italic"), 
                foreground=self.COLORS['accent'], bg=self.COLORS['background']).pack(pady=(0, 50))
        
        # User Mode Button
        user_btn = ttk.Button(center, text="🎵 USER MODE\nDengarkan Musik Favorit", 
                              command=lambda: self.login_as("user"), style='Large.TButton')
        user_btn.pack(pady=15, ipadx=50, ipady=20)
        ToolTip(user_btn, "Masuk sebagai User untuk mendengarkan musik")
        
        # Admin Mode Button
        admin_btn = ttk.Button(center, text="⚙️ ADMIN MODE\nKelola Library Musik", 
                               command=lambda: self.login_as("admin"), style='Large.TButton')
        admin_btn.pack(pady=15, ipadx=50, ipady=20)
        ToolTip(admin_btn, "Masuk sebagai Admin untuk mengelola library")

    def login_as(self, mode):
        """Login as user or admin"""
        self.current_mode = mode
        if mode == "user":
            self.show_home_screen()
        else:
            self.show_admin_screen()

    # ============= HOME SCREEN (USER) =============
    def show_home_screen(self):
        """Show user home screen"""
        screen = self.clear_screen()
        
        # Header
        header = tk.Frame(screen, bg=self.COLORS['background'])
        header.pack(fill="x", padx=30, pady=20)
        
        tk.Label(header, text="🌅 SUNSCAPE", font=("Segoe UI", 24, "bold"), 
                foreground=self.COLORS['primary'], bg=self.COLORS['background']).pack(side="left")
        
        tk.Label(header, text=f"👤 {self.current_user.username}", font=("Segoe UI", 14), 
                foreground=self.COLORS['text'], bg=self.COLORS['background']).pack(side="right")
        
        # Stats cards
        stats_frame = tk.Frame(screen, bg=self.COLORS['background'])
        stats_frame.pack(fill="x", padx=30, pady=20)
        
        # Stats card 1
        card1 = tk.Frame(stats_frame, bg=self.COLORS['card'], relief="flat", bd=2)
        card1.pack(side="left", fill="both", expand=True, padx=10)
        tk.Label(card1, text="📊 Statistics", font=("Segoe UI", 14, "bold"), 
                foreground=self.COLORS['primary'], bg=self.COLORS['card']).pack(pady=10)
        self.stats_label = tk.Label(card1, text=f"{len(self.songs_played)} songs played", 
                                    font=("Segoe UI", 12), foreground=self.COLORS['text'], bg=self.COLORS['card'])
        self.stats_label.pack(pady=10)
        
        # Random play card
        card2 = tk.Frame(stats_frame, bg=self.COLORS['card'], relief="flat", bd=2)
        card2.pack(side="left", fill="both", expand=True, padx=10)
        random_btn = ttk.Button(card2, text="🎵 Play Random", command=self._play_random_song, style='Fun.TButton')
        random_btn.pack(pady=30, padx=20)
        ToolTip(random_btn, "Play a random song from library")
        
        # Quick Access
        tk.Label(screen, text="Quick Access:", font=("Segoe UI", 16, "bold"), 
                foreground=self.COLORS['text'], bg=self.COLORS['background']).pack(anchor="w", padx=30, pady=(20, 10))
        
        quick_frame = tk.Frame(screen, bg=self.COLORS['background'])
        quick_frame.pack(fill="x", padx=30)
        
        # Playlist button
        playlist_card = tk.Frame(quick_frame, bg=self.COLORS['card'], relief="flat", bd=2)
        playlist_card.pack(side="left", padx=10, pady=10)
        playlist_btn = ttk.Button(playlist_card, text="⭐\nPlaylists", command=self.show_playlist_screen, style='Fun.TButton')
        playlist_btn.pack(padx=30, pady=20)
        ToolTip(playlist_btn, "Manage your playlists")
        
        # Search button
        search_card = tk.Frame(quick_frame, bg=self.COLORS['card'], relief="flat", bd=2)
        search_card.pack(side="left", padx=10, pady=10)
        search_btn = ttk.Button(search_card, text="🔍\nSearch", command=self.show_search_screen, style='Fun.TButton')
        search_btn.pack(padx=30, pady=20)
        ToolTip(search_btn, "Search for songs")
        
        # Recent activity
        tk.Label(screen, text="📝 Recent Activity:", font=("Segoe UI", 16, "bold"), 
                foreground=self.COLORS['text'], bg=self.COLORS['background']).pack(anchor="w", padx=30, pady=(20, 10))
        
        recent_frame = tk.Frame(screen, bg=self.COLORS['card'])
        recent_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        self.recent_listbox = tk.Listbox(recent_frame, height=8, font=("Courier", 10), 
                                         selectbackground=self.COLORS['button'], selectforeground='white',
                                         bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0)
        self.recent_listbox.pack(fill="both", expand=True, padx=10, pady=10)

    # Placeholder methods - will implement next
    def show_admin_screen(self):
        pass
    
    def show_playlist_screen(self):
        pass
    
    def show_search_screen(self):
        pass
    
    def _play_random_song(self):
        pass
    
    def _toggle_play_stop(self):
        pass
    
    def _next_song(self):
        pass
    
    def _prev_song(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayerApp(root)
    root.mainloop()
