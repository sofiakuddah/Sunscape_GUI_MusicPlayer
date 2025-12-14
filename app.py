import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
import random
import re
from datetime import datetime
from tkinter import filedialog  # Add filedialog

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


# Import dari models dan utils menggunakan import relatif
from ..models.doubly_linked_list import DoublyLinkedList
from ..models.song import Song
from ..models.playlist import Playlist
from ..models.user import UserManager, PlayerStack, SmartQueue
from ..models.user import UserManager, PlayerStack, SmartQueue
from ..utils.helpers import levenshtein_distance, fisher_yates_shuffle
from ..utils.persistence import PersistenceManager  # NEW: Persistence


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
            self.window.attributes('-topmost', True) # Re-assert topmost
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("🌅 SUNSCAPE Player")
        
        # Calculate Center Position relative to Parent
        w = 400
        h = 350
        
        try:
            # Get parent geometry
            mx = self.parent.winfo_rootx()
            my = self.parent.winfo_rooty()
            mw = self.parent.winfo_width()
            mh = self.parent.winfo_height()
            
            x = mx + (mw // 2) - (w // 2)
            y = my + (mh // 2) - (h // 2)
        except:
            # Fallback if parent geometry fails
            x = 100
            y = 100
            
        self.window.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
        self.window.resizable(False, False)
        self.window.attributes('-topmost', True)
        self.window.configure(bg=self.app.COLORS['background'])  # Deep Night Blue
        
        # Force lift
        self.window.lift()
        self.window.focus_force()
        
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
        control_frame.pack(pady=15)
        
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
        """Tutup window dengan benar - FIX BUG #5: Stop audio saat popup ditutup"""
        # Stop timer safely
        self.stop_timer()
        
        # FIX BUG #5: Stop audio playback
        if PYGAME_AVAILABLE and not self.app.pygame_error:
            try:
                pygame.mixer.music.stop()
            except:
                pass
        
        # Update app state
        self.app.is_playing = False
        
        # Destroy window
        try:
            if self.window and hasattr(self.window, 'winfo_exists') and self.window.winfo_exists():
                self.window.destroy()
        except:
            pass
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
        """Mulai timer dari 0 (New/Replay)"""
        try:
            self.stop_timer()
            self.elapsed_seconds = 0
            self._update_timer()
        except Exception as e:
            print(f"DEBUG: Start timer error: {e}")

    def resume_timer(self):
        """Lanjut timer dari posisi terakhir (Unpause)"""
        try:
            self.stop_timer()
            self._update_timer()
        except Exception as e:
            print(f"DEBUG: Resume timer error: {e}")
    
    def _update_timer(self):
        """Update progress bar setiap 1 DETIK (1000ms)"""
        # FIX: Check window exists before doing anything
        if not self.window or not hasattr(self.window, 'winfo_exists'):
            return
        
        try:
            if not self.window.winfo_exists():
                return
        except:
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
        # FIX: Check window still exists before scheduling next update
        try:
            if self.window and hasattr(self.window, 'after') and hasattr(self.window, 'winfo_exists'):
                if self.window.winfo_exists():
                    self.timer_id = self.window.after(1000, self._update_timer)
        except:
            pass
    
    def stop_timer(self):
        """Stop timer - FIX: Check window exists before canceling"""
        if self.timer_id:
            try:
                if self.window and hasattr(self.window, 'after_cancel'):
                    self.window.after_cancel(self.timer_id)
            except:
                pass
            self.timer_id = None


class MusicPlayerApp:
    def __init__(self, master):
        self.master = master
        master.title("🌅 SUNSCAPE: Musik, senja, dan kamu.")
        master.geometry("950x700")
        master.resizable(True, True)
        
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
        self.style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=[20, 10], 
                            background=self.COLORS['card'], foreground=self.COLORS['text_secondary'])
        self.style.map('TNotebook.Tab', 
                      background=[('selected', self.COLORS['button'])], 
                      foreground=[('selected', 'white')])
        
        # Frame Styling
        self.style.configure('TFrame', background=self.COLORS['background'])
        self.style.configure('Card.TFrame', background=self.COLORS['card']) # Container beda warna
        
        # LabelFrame Styling - Lebih Rapi
        self.style.configure('TLabelframe', background=self.COLORS['background'], foreground=self.COLORS['primary'], relief='flat')
        self.style.configure('TLabelframe.Label', background=self.COLORS['background'], foreground=self.COLORS['primary'], font=('Segoe UI', 11, 'bold'))
        
        # Label Styling
        self.style.configure('TLabel', background=self.COLORS['background'], foreground=self.COLORS['text'])
        self.style.configure('Card.TLabel', background=self.COLORS['card'], foreground=self.COLORS['text'])
        
        # Button Styling (Sunscape Premium Buttons)
        self.style.configure('Fun.TButton', font=('Segoe UI', 10, 'bold'), 
                            foreground='white', background=self.COLORS['button'], borderwidth=0, padding=10)
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
        
        # PERSISTENCE: Load data or seed
        data_loaded = PersistenceManager.load_data(self.library, self.user_manager)
        if not data_loaded:
            print("No data found, seeding defaults...")
            # RESET STATE to ensure clean seed (fix KeyError U001 issues)
            self.library = DoublyLinkedList()
            self.user_manager = UserManager()
            self._seed_data()
        else:
             print("Data loaded from persistence.")

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
        
        # Save on exit
        master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Current mode tracking
        self.current_mode = None  # "user" or "admin"
        self.current_screen_name = None
        
        # SELECTION CACHE (Fix for focus loss issues)
        self.selected_song_cache = None # Stores Song object
        self.selected_context = None # "library", "playlist", "search"
        
        # Audio Initialization
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"Error initializing mixer: {e}")
                self.pygame_error = True
            else:
                self.pygame_error = False
        else:
            self.pygame_error = True
        
        # Main container for all screens
        self.main_container = tk.Frame(master, bg=self.COLORS['background'])
        self.main_container.pack(fill="both", expand=True)
        
        # Frames will be created on demand
        self.home_frame = None
        self.admin_frame = None
        self.search_queue_frame = None
        self.playlist_frame = None
        
        # Show login screen first
        self.show_login_screen()

    def on_closing(self):
        """Handle apps closing - FIX BUG #4: Pastikan GUI bisa di-exit"""
        try:
            # Stop audio
            if PYGAME_AVAILABLE and not self.pygame_error:
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                except:
                    pass
            
            # Save data
            self._save_data()
            
            # Close floating player
            self.floating_player.close_window()
        except:
            pass
        finally:
            # Force destroy
            self.master.quit()
            self.master.destroy()

    def _save_data(self):
        """Save data to JSON"""
        PersistenceManager.save_data(self.library, self.user_manager)
        # print("Autosave: Data saved.")

    def _show_toast(self, message: str):
        """Show non-blocking toast notification (POPUP RESTORED)"""
        try:
            # Clean up old toast
            if hasattr(self, 'current_toast') and self.current_toast:
                try:
                    self.current_toast.destroy()
                except:
                    pass
            
            # Create NEW toast on master (Independent of main_container)
            self.current_toast = tk.Frame(self.master, bg="#333333", padx=25, pady=12, highlightthickness=1, highlightbackground="white")
            
            # Place Top Center (approx 15% from top)
            self.current_toast.place(relx=0.5, rely=0.15, anchor="center")
            
            tk.Label(self.current_toast, text=message, fg="white", bg="#333333", 
                    font=("Segoe UI", 11, "bold")).pack()
            
            # FORCE ON TOP
            self.current_toast.lift()
            
            # Auto cleanup
            def fade_destroy():
                try:
                    if hasattr(self, 'current_toast') and self.current_toast:
                        self.current_toast.destroy()
                except:
                    pass
            
            self.master.after(3000, fade_destroy)
            
        except Exception as e:
            print(f"DEBUG: Toast error: {e}")


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
        self.home_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Add logout button at top
        header = tk.Frame(self.home_frame, bg=self.COLORS['background'])
        header.pack(fill="x", pady=(0, 10))
        
        logout_btn = ttk.Button(header, text="🚪 Logout", command=self.show_login_screen, style='Fun.TButton')
        logout_btn.pack(side="right")
        ToolTip(logout_btn, "Back to Login")
        
        # Setup home UI
        self._setup_home_ui(self.home_frame)
        
        # FIX BUG #3 & #4: Initialize statistics display after UI is created
        self._initialize_home_statistics()
    
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
        
        # Populate library list after widgets are created
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
        
        # Populate queue list after widgets are created
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
        
        # Populate playlist list after widgets are created
        self._update_playlist_listbox()

    def _seed_data(self):
        """Inisialisasi data dummy - HANYA struktur user dan playlist, TANPA lagu"""
        # Default user dengan hanya 2 playlist (KOSONG)
        default_user = self.user_manager.add_user("Zalsa")
        self.user_manager.add_playlist(default_user.id, "My Playlist")
        self.user_manager.add_playlist(default_user.id, "Favorites")
        # NOTE: Library dan playlist dimulai KOSONG - admin akan menambahkan lagu manual


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
        """Update library listbox - FIX BUG #6"""
        try:
             # FIX BUG #6: Better widget existence check
             if not hasattr(self, 'library_listbox'):
                 print("DEBUG: library_listbox attribute doesn't exist")
                 return
             if not self.library_listbox:
                 print("DEBUG: library_listbox is None")
                 return
             if not hasattr(self.library_listbox, 'winfo_exists') or not self.library_listbox.winfo_exists():
                 print("DEBUG: library_listbox widget doesn't exist")
                 return
             
             songs = self.library.get_all_songs()
             print(f"DEBUG: Updating library listbox with {len(songs)} songs")
             formatted_songs = self._format_library_list(songs)
             self.library_listbox.delete(0, tk.END)
             for song_line in formatted_songs:
                 self.library_listbox.insert(tk.END, song_line)
        except Exception as e:
             print(f"DEBUG: Update listbox error: {e}")

    # ============= TAB 1: HOME UI (USER DASHBOARD) =============
    def _setup_home_ui(self, frame):
        """Setup HOME tab dengan user dashboard"""
        # Header with logo
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
                foreground=self.COLORS['accent'], bg=self.COLORS['background']).pack(anchor='w')
        
        # User Profile Section - COMPACT
        profile_frame = ttk.LabelFrame(frame, text="👤 Profile", padding="12", style='TLabelframe')
        profile_frame.pack(fill="x", pady=8, padx=15)
        
        ttk.Label(profile_frame, text=f"{self.current_user.username}", font=("Segoe UI", 18, "bold"), foreground='white').pack(anchor='w', pady=(0,3))
        ttk.Label(profile_frame, text=f"ID: {self.current_user.id}  •  Since {datetime.now().strftime('%b %Y')}", 
                 font=("Segoe UI", 9), foreground=self.COLORS['text_secondary']).pack(anchor='w')
        
        # Statistics Section - COMPACT
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
        self.most_artist_label.pack(anchor='w', pady=(0, 8))
        
        # Quick Actions - COMPACT
        actions_frame = ttk.LabelFrame(frame, text="⚡ Quick Access", padding="10", style='TLabelframe')
        actions_frame.pack(fill="x", pady=8, padx=15)
        
        action_buttons = ttk.Frame(actions_frame, style='TFrame')
        action_buttons.pack(fill="x", pady=5)
        
        ttk.Button(action_buttons, text="🎵 Random", command=self._play_random_song, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=3)
        ttk.Button(action_buttons, text="⭐ Playlists", command=self.show_playlist_screen, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=3)
        ttk.Button(action_buttons, text="🔍 Search", command=self.show_search_screen, style='Fun.TButton').pack(side="left", fill="x", expand=True, padx=3)
        
        # Recent Activity - COMPACT
        activity_frame = ttk.LabelFrame(frame, text="📝 Recent", padding="10", style='TLabelframe')
        activity_frame.pack(fill="both", expand=True, pady=8, padx=15)
        
        ttk.Label(activity_frame, text="Recently played:", font=("Segoe UI", 8, "italic"), foreground=self.COLORS['text_secondary']).pack(anchor='w', pady=(0, 5))
        
        recent_container = ttk.Frame(activity_frame)
        recent_container.pack(fill="both", expand=True)
        
        self.recent_listbox = tk.Listbox(recent_container, height=8, font=("Consolas", 9), 
                                         selectbackground=self.COLORS['button'], selectforeground='white',
                                         bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0,
                                         exportselection=False)
        self.recent_listbox.pack(side="left", fill="both", expand=True)
        
        scroll = ttk.Scrollbar(recent_container, orient="vertical", command=self.recent_listbox.yview)
        scroll.pack(side="right", fill="y")
        self.recent_listbox.config(yscrollcommand=scroll.set)
    
    def _initialize_home_statistics(self):
        """Initialize statistics display on home screen - FIX BUG #3 & #4"""
        try:
            # Update total songs played
            if hasattr(self, 'total_songs_label') and self.total_songs_label and self.total_songs_label.winfo_exists():
                self.total_songs_label.config(text=str(len(self.songs_played)))
            
            # Update total minutes
            if hasattr(self, 'total_minutes_label') and self.total_minutes_label and self.total_minutes_label.winfo_exists():
                total_minutes = int(self.total_play_time / 60)
                self.total_minutes_label.config(text=f"{total_minutes} min")
            
            # Update favorite genre
            if self.songs_played and hasattr(self, 'fav_genre_label') and self.fav_genre_label and self.fav_genre_label.winfo_exists():
                genres = [s.genre for s in self.songs_played]
                fav_genre = max(set(genres), key=genres.count)
                self.fav_genre_label.config(text=fav_genre)
            
            # Update most played artist
            if self.songs_played and hasattr(self, 'most_artist_label') and self.most_artist_label and self.most_artist_label.winfo_exists():
                artists = [s.artist for s in self.songs_played]
                most_artist = max(set(artists), key=artists.count)
                self.most_artist_label.config(text=most_artist)
            
            # Update recent activity
            if hasattr(self, 'recent_listbox') and self.recent_listbox and self.recent_listbox.winfo_exists():
                self.recent_listbox.delete(0, tk.END)
                # Show last 10 songs in reverse order (most recent first)
                for song in reversed(self.songs_played[-10:]):
                    self.recent_listbox.insert(tk.END, f"► {song.title} - {song.artist}")
        except Exception as e:
            print(f"DEBUG: Initialize stats error: {e}")
    
        # ============= TAB 2: ADMIN UI =============
    def _setup_admin_ui(self, frame):
        """Setup ADMIN tab untuk library control"""
        header_frame = ttk.Frame(frame, padding="10 10 10 5", style='TFrame')
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="🔑 Admin Panel", font=("Segoe UI", 16, "bold"), foreground=self.COLORS['primary']).pack(anchor='w')
        ttk.Label(header_frame, text="Manage library - changes sync to all users", font=("Segoe UI", 9, "italic"), foreground=self.COLORS['text_secondary']).pack(anchor='w')
        
        action_frame = ttk.Frame(frame, padding="8 0", style='TFrame')
        action_frame.pack(fill="x", pady=8)
        ttk.Button(action_frame, text="➕ Add", command=self.open_add_dialog, style='Fun.TButton').pack(side="left", padx=5)
        ttk.Button(action_frame, text="✏️ Edit", command=self.open_edit_dialog, style='Fun.TButton').pack(side="left", padx=5)
        ttk.Button(action_frame, text="❌ Delete", command=self._delete_song_action, style='Fun.TButton').pack(side="left", padx=5)
        
        list_header_frame = ttk.Frame(frame, padding="8 5 8 0", style='TFrame')
        list_header_frame.pack(fill="x")
        ttk.Label(list_header_frame, text="ID | Title | Artist | Genre | Year | Duration", font=("Courier", 8, "bold"), foreground=self.COLORS['accent']).pack(anchor="w")
        
        listbox_frame = ttk.Frame(frame, padding="8 5", style='TFrame')
        listbox_frame.pack(fill="both", expand=True)
        self.library_listbox = tk.Listbox(listbox_frame, height=15, font=("Consolas", 9), bd=0, highlightthickness=0, 
                                          selectbackground=self.COLORS['button'], selectforeground='white',
                                          bg=self.COLORS['card'], fg='white', exportselection=False)
        self.library_listbox.pack(side="left", fill="both", expand=True)
        self.library_listbox.bind('<<ListboxSelect>>', lambda e: self._on_song_select(e, "library"))
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.library_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.library_listbox.config(yscrollcommand=scrollbar.set)

    # ============= TAB 3: CARI & ANTRIAN UI =============
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
        # FIX BUG #5: Add ID search option
        tk.Radiobutton(search_input, text="ID", variable=search_by_var, value="id",
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
        self.search_listbox = tk.Listbox(listbox_container, height=9, font=("Consolas", 9), 
                                         selectbackground=self.COLORS['button'], selectforeground='white',
                                         bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0,
                                         exportselection=False)
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
        self.queue_listbox = tk.Listbox(queue_listbox_container, height=9, font=("Consolas", 9), 
                                        selectbackground=self.COLORS['button'], selectforeground='white',
                                        bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0,
                                        exportselection=False)
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
        ToolTip(qb5, "Save as playlist")

    # ============= TAB 4: PLAYLIST UI =============
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
        self.playlist_listbox = tk.Listbox(listbox_container, height=12, font=("Consolas", 9), 
                                           selectbackground=self.COLORS['button'], selectforeground='white',
                                           bg=self.COLORS['card'], fg='white', borderwidth=0, highlightthickness=0,
                                           exportselection=False)
        self.playlist_listbox.pack(side="left", fill="both", expand=True)
        self.playlist_listbox.bind('<<ListboxSelect>>', lambda e: self._on_song_select(e, "playlist"))
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
        ToolTip(delete_btn, "Delete entire playlist")

    # ============= PLAYER METHODS =============
    def _play_random_song(self):
        """Play lagu secara urut dari library admin (PURE SEQUENTIAL)"""
        try:
            all_songs = self.library.get_all_songs()
            if not all_songs:
                messagebox.showwarning("Peringatan", "Library kosong!")
                return
            
            # Play lagu pertama dari library (urut sesuai admin library)
            first_song = all_songs[0]
            
            # Set index untuk tracking
            self.current_library_index = 0
            
            # PENTING: Gunakan context "library_sequential" untuk pure urutan
            self._start_playing_song(first_song, "library_sequential")
            print(f"DEBUG: Playing first song from library (sequential mode): {first_song.title}")
            
            try:
                self._show_toast(f"▶️ Memutar: {first_song.title}")
            except:
                pass
            
        except Exception as e:
            print(f"DEBUG: Play from library error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Terjadi kesalahan saat memutar lagu:\n{str(e)}")



    def _start_playing_song(self, song: Song, context: str):
        """Helper method untuk memulai playback dengan tracking statistik"""
        try:
            # Stop timer lama
            self.floating_player.stop_timer()
            
            # Stop audio lama (jika ada)
            if PYGAME_AVAILABLE and not self.pygame_error:
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                except:
                    pass
            
            self.current_playing_song = song
            self.is_playing = True
            self.playback_context = context
            
            # --- REAL AUDIO LOGIC ---
            if song.file_path:
                if PYGAME_AVAILABLE and not self.pygame_error:
                    try:
                        pygame.mixer.music.load(song.file_path)
                        pygame.mixer.music.play()
                        print(f"DEBUG: Playing audio file: {song.file_path}")
                    except Exception as e:
                        print(f"DEBUG: Audio playback error: {e}")
                        # Don't show popup, just log
                else:
                    print("DEBUG: Pygame not available, running simulation mode")
            else:
                 print(f"DEBUG: No file path for song {song.title}. Simulation mode.")
            
            # Track play time (SAFE MODE)
            try:
                duration_sec = self._parse_duration_to_seconds(song.duration)
                self.total_play_time += duration_sec
            except Exception as e:
                print(f"DEBUG: Duration tracking error: {e}")
            
            # Update statistics (SAFE MODE)
            try:
                self._update_statistics(song)
            except Exception as e:
                print(f"DEBUG: Statistics update error: {e}")
            
            # Show player (CRITICAL - MUST RUN)
            try:
                self._show_floating_player()
                self.floating_player.update_display(song, True)
                self.floating_player.start_timer()
            except Exception as e:
                print(f"DEBUG: Player Window Error: {e}")
                import traceback
                traceback.print_exc()
            
            # NOTIFICATION: Show toast (CRITICAL - MUST RUN)
            try:
                self._show_toast(f"Now Playing: {song.title}")
            except Exception as e:
                print(f"DEBUG: Toast Error: {e}")
        except Exception as e:
            print(f"DEBUG: Critical error in _start_playing_song: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Gagal memulai playback:\n{str(e)}")
    
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
        """Update statistik user (Crash-proof) - FIX BUG #3 & #4"""
        try:
            # FIX BUG #4: Always add to songs_played for activity tracking
            if song not in self.songs_played:
                self.songs_played.append(song)
            else:
                # Even if song was played before, add it again for activity tracking
                self.songs_played.append(song)
            
            # Helper for safe widget update
            def safe_config(widget, **kwargs):
                try:
                    if widget and hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                        widget.config(**kwargs)
                except:
                    pass

            # FIX BUG #4: Update recent activity - ALWAYS try to update
            try:
                if hasattr(self, 'recent_listbox') and self.recent_listbox:
                    if hasattr(self.recent_listbox, 'winfo_exists') and self.recent_listbox.winfo_exists():
                        self.recent_listbox.insert(0, f"► {song.title} - {song.artist}")
                        if self.recent_listbox.size() > 10:
                            self.recent_listbox.delete(10, tk.END)
            except Exception as e:
                print(f"DEBUG: Recent activity update error: {e}")
            
            # FIX BUG #3: Update statistics display with better checks
            if hasattr(self, 'total_songs_label'):
                safe_config(self.total_songs_label, text=str(len(self.songs_played)))
            
            # Update total minutes
            if hasattr(self, 'total_minutes_label'):
                total_minutes = int(self.total_play_time / 60)
                safe_config(self.total_minutes_label, text=f"{total_minutes} min")
            
            # Calculate favorite genre
            if self.songs_played and hasattr(self, 'fav_genre_label'):
                genres = [s.genre for s in self.songs_played]
                fav_genre = max(set(genres), key=genres.count)
                safe_config(self.fav_genre_label, text=fav_genre)
            
            # Calculate most played artist
            if self.songs_played and hasattr(self, 'most_artist_label'):
                artists = [s.artist for s in self.songs_played]
                most_artist = max(set(artists), key=artists.count)
                safe_config(self.most_artist_label, text=most_artist)
        except Exception as e:
            print(f"DEBUG: Stats update error: {e}")

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
        
        # File Path Input
        file_path_var = tk.StringVar()
        ttk.Label(input_frame, text="File Audio (Opsional):").grid(row=5, column=0, sticky="w", pady=5)
        path_entry = ttk.Entry(input_frame, textvariable=file_path_var, width=22)
        path_entry.grid(row=5, column=1, sticky="w", pady=5, padx=5)
        
        def browse_file():
            filename = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3;*.wav;*.ogg;*.mp4;*.m4a;*.flac")])
            if filename:
                file_path_var.set(filename)
                
        ttk.Button(input_frame, text="Browse", command=browse_file, width=6).grid(row=5, column=1, sticky="e", padx=5)
        
        def submit():
            title = title_var.get().strip()
            artist = artist_var.get().strip()
            genre = genre_var.get().strip()
            year = year_var.get().strip()
            duration = duration_var.get().strip()
            fpath = file_path_var.get().strip()
            
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

            if self.library.add_song(title, artist, genre, year, duration, fpath):
                messagebox.showinfo("Sukses", f"Lagu '{title}' berhasil ditambahkan!")
                self._save_data()  # Autosave
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

        # File Path Input (Edit)
        file_path_var = tk.StringVar(value=getattr(old_song, 'file_path', ''))
        ttk.Label(input_frame, text="File Audio:").grid(row=5, column=0, sticky="w", pady=5)
        path_entry = ttk.Entry(input_frame, textvariable=file_path_var, width=22)
        path_entry.grid(row=5, column=1, sticky="w", pady=5, padx=5)
        
        def browse_edit_file():
            filename = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3;*.wav;*.ogg;*.mp4;*.m4a;*.flac")])
            if filename:
                file_path_var.set(filename)
                
        ttk.Button(input_frame, text="Browse", command=browse_edit_file, width=6).grid(row=5, column=1, sticky="e", padx=5)
        
        def submit():
            new_title = title_var.get().strip()
            new_artist = artist_var.get().strip()
            new_genre = genre_var.get().strip()
            new_year = year_var.get().strip()
            new_duration = duration_var.get().strip()
            new_fpath = file_path_var.get().strip()
            
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
                
            if self.library.edit_song(song_id, new_title, new_artist, new_genre, new_year, new_duration, new_fpath):
                messagebox.showinfo("Sukses", f"Lagu ID {song_id} berhasil diupdate!")
                self._save_data()  # Autosave
                self._update_listbox()
                self._update_playlist_listbox()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Gagal mengedit lagu.")
        
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill="x")
        ttk.Button(button_frame, text="OK", command=submit, style='Fun.TButton').pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)

    def _delete_song_action(self):
        """Action delete song (Fix selection loss)"""
        try:
            # TRY 1: Direct selection
            selection = None
            try:
                selection = self.library_listbox.curselection()
            except Exception:
                pass

            song_id = None
            
            if selection:
                 try:
                     selected_line = self.library_listbox.get(selection[0])
                     song_id = selected_line.split(' | ')[0].strip()
                 except Exception:
                     pass
            
            # TRY 2: Cache fallback
            if not song_id and self.selected_song_cache and self.selected_context == "library":
                 song_id = self.selected_song_cache.id
            
            if not song_id:
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
                    
                    self._save_data()  # Autosave
                    messagebox.showinfo("Sukses", f"Lagu ID {song_id} berhasil dihapus!")
                    self._update_listbox()
                    self._update_playlist_listbox()
                else:
                    messagebox.showerror("Error", "Gagal menghapus lagu.")
        except Exception:
            pass

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
        """Tambah lagu dari search ke playlist (Fix selection loss)"""
        try:
             # TRY 1: Direct selection
            selection = None
            try:
                selection = self.search_listbox.curselection()
            except Exception:
                pass

            song_id = None
            
            if selection:
                try:
                    selected_line = self.search_listbox.get(selection[0])
                    if "Tidak ditemukan" in selected_line or "kosong" in selected_line.lower():
                         messagebox.showwarning("Peringatan", "Pilih lagu yang valid!")
                         return
                    song_id = selected_line.split(' | ')[0].strip()
                except Exception:
                    pass
            
            # TRY 2: Cache fallback
            if not song_id and self.selected_song_cache and self.selected_context in ["search", "library"]:
                 song_id = self.selected_song_cache.id
        
            if not song_id:
                messagebox.showwarning("Peringatan", "Pilih lagu dari hasil pencarian dulu!")
                return
            
            try:
                target_name = self.target_playlist_var.get()
            except Exception:
                pass
        except Exception:
            pass
        
        target_playlist = self.current_user.playlists.get(target_name)
        if not target_playlist:
            messagebox.showerror("Error", f"Playlist '{target_name}' tidak ditemukan!")
            return
        
        # TAMBAH KE PLAYLIST
        if target_playlist.add_song(song_id):
            self._save_data()  # Autosave
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

    # FIX BUG #2: Play dari search - pastikan popup muncul
    def _play_from_library(self):
        """Play lagu dari search results - Gunakan logika kemiripan"""
        try:
            # Better error handling and validation
            if not hasattr(self, 'search_listbox') or not self.search_listbox:
                messagebox.showerror("Error", "Search listbox tidak tersedia!")
                return
            
            selection = self.search_listbox.curselection()
            if not selection:
                messagebox.showwarning("Peringatan", "Pilih lagu dari hasil pencarian dulu!")
                return
            
            selected = self.search_listbox.get(selection[0])
            if "Tidak ditemukan" in selected or "kosong" in selected.lower():
                messagebox.showwarning("Peringatan", "Pilih lagu yang valid!")
                return
            
            song_id = selected.split(' | ')[0].strip()
            song = self.library.id_map.get(song_id)
            if song:
                # Set index di library
                all_songs = self.library.get_all_songs()
                try:
                    self.current_library_index = next(i for i, s in enumerate(all_songs) if s.id == song_id)
                except StopIteration:
                    self.current_library_index = 0
                
                # PENTING: Gunakan context "library_similar" untuk logika kemiripan
                print(f"DEBUG: Playing from search (similar mode): {song.title}")
                self._start_playing_song(song, "library_similar")
            else:
                messagebox.showerror("Error", "Lagu tidak ditemukan di library.")
        except tk.TclError as e:
            print(f"DEBUG: TclError in play from library: {e}")
            messagebox.showwarning("Peringatan", "Pilih lagu dari hasil pencarian dulu!")
        except Exception as e:
            print(f"DEBUG: Play from library error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Gagal memutar lagu dari pencarian:\n{str(e)}")

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
            self._save_data()  # Autosave
            song = self.library.id_map.get(song_id)
            title = song.title if song else song_id
            messagebox.showinfo("❤️ Berhasil!", f"'{title}' telah ditambahkan ke Favorites!")
            if self.current_playlist_name == "Favorites":
                self._update_playlist_listbox()
        else:
            messagebox.showinfo("ℹ️", "Lagu ini sudah ada di Favorites!")

    # ============= QUEUE METHODS =============
    # FIX BUG #2: Play dari queue dengan popup player
    def _play_from_queue(self):
        """Play lagu pertama dari queue - FIX BUG #2: Pastikan popup muncul"""
        try:
            # FIX BUG #2: Better validation
            if not hasattr(self, 'smart_queue') or not self.smart_queue:
                messagebox.showerror("Error", "Queue tidak tersedia!")
                return
            
            # FIX: Use size check instead of .queue list check
            if self.smart_queue.size == 0:
                messagebox.showwarning("Peringatan", "Antrian kosong!")
                return
            
            # Ambil lagu pertama - FIX: Use pop_next() because SmartQueue is a linked list
            song = self.smart_queue.pop_next()
            
            if not song:
                messagebox.showerror("Error", "Lagu di queue tidak valid!")
                return
            
            # Update listbox setelah pop
            self._update_queue_listbox()
            
            # FIX BUG #2: PUTAR dengan popup player (menggunakan helper method)
            print(f"DEBUG: Playing from queue: {song.title}")
            self._start_playing_song(song, "queue")
        except Exception as e:
            print(f"DEBUG: Play from queue error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Gagal memutar lagu dari queue:\n{str(e)}")
    
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
                    self._save_data()  # Autosave
                    self._clear_queue()
                    
                    # FIX: Update dropdown only if widgets still exist
                    playlist_names = list(self.current_user.playlists.keys())
                    try:
                        if hasattr(self, 'active_playlist_dropdown') and self.active_playlist_dropdown:
                            if hasattr(self.active_playlist_dropdown, 'winfo_exists') and self.active_playlist_dropdown.winfo_exists():
                                self.active_playlist_dropdown['values'] = playlist_names
                    except:
                        pass
                    try:
                        if hasattr(self, 'playlist_dropdown') and self.playlist_dropdown:
                            if hasattr(self.playlist_dropdown, 'winfo_exists') and self.playlist_dropdown.winfo_exists():
                                self.playlist_dropdown['values'] = playlist_names
                    except:
                        pass
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
        """Play lagu yang dipilih dari playlist - FIX BUG #1: Set current_play pointer"""
        try:
            # FIX BUG #1: Better validation
            if not hasattr(self, 'playlist_listbox') or not self.playlist_listbox:
                messagebox.showerror("Error", "Playlist listbox tidak tersedia!")
                return
            
            # TRY 1: Direct selection
            selection = None
            try:
                selection = self.playlist_listbox.curselection()
            except Exception as e:
                print(f"DEBUG: Selection error: {e}")
            
            song_id = None
            if selection:
                try:
                    selected_line = self.playlist_listbox.get(selection[0])
                    if "kosong" in selected_line.lower():
                        messagebox.showwarning("Peringatan", "Playlist kosong!")
                        return
                    song_id = selected_line.split(' | ')[0].strip()
                except Exception as e:
                    print(f"DEBUG: Get selection error: {e}")
            
            # TRY 2: Cache fallback
            if not song_id and self.selected_song_cache and self.selected_context == "playlist":
                song_id = self.selected_song_cache.id
                print(f"DEBUG: Using cached song: {song_id}")
                
            if not song_id:
                messagebox.showwarning("Peringatan", "Pilih lagu dari Playlist.")
                return

            target_song = self.library.id_map.get(song_id)
            if target_song:
                # FIX BUG #1: Set context ke playlist dan set current_play pointer
                if self.shuffle_enabled and self.shuffled_order:
                    try:
                        self.current_index_in_shuffle = self.shuffled_order.index(song_id)
                    except ValueError:
                        self.current_index_in_shuffle = 0
                else:
                    # FIX BUG #1: CRITICAL - Set current_play pointer untuk prev/next
                    if self.current_playlist:
                        self.current_playlist.set_current_song(song_id)
                        print(f"DEBUG: Set current_play pointer to {song_id}")
                
                print(f"DEBUG: Playing from playlist: {target_song.title}")
                self._start_playing_song(target_song, "playlist")
            else:
                messagebox.showerror("Error", "Lagu tidak ditemukan.")

        except Exception as e:
            print(f"DEBUG: Play from playlist error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Gagal memutar lagu dari playlist:\n{str(e)}")

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
                self._save_data()  # Autosave
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

    # ============= HELPER Methods =============
    def _on_song_select(self, event, context):
        """Handle selection event to cache song"""
        try:
            widget = event.widget
            selection = widget.curselection()
            if selection:
                index = selection[0]
                data = widget.get(index)
                
                # Parse ID from string "ID | Title..."
                 # Format check
                if " | " in data:
                    song_id = data.split(' | ')[0].strip()
                    song = self.library.id_map.get(song_id)
                    if song:
                        self.selected_song_cache = song
                        self.selected_context = context
                        # print(f"DEBUG: Selected {song.title} from {context}")
        except:
            pass

    def _delete_current_playlist(self):
        """Hapus playlist saat ini"""
        name = self.current_playlist_name
        if name == "My Playlist" or name == "Favorites":
             messagebox.showwarning("Peringatan", "Playlist default tidak bisa dihapus!")
             return
             
        if messagebox.askyesno("Konfirmasi", f"Yakin menghapus playlist '{name}'?"):
            if self.user_manager.remove_playlist(self.current_user.id, name):
                messagebox.showinfo("Sukses", "Playlist dihapus.")
                self._save_data()  # Autosave
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
        try:
            if not hasattr(self, 'playlist_listbox') or not self.playlist_listbox or not self.playlist_listbox.winfo_exists():
                return

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
        except:
            pass

    # ============= PLAYER CONTROLS =============
    def _toggle_play_stop(self):
        """Toggle play/stop - FIX BUG #6: Jangan reset durasi saat pause"""
        if self.is_playing:
            # PAUSE
            self.is_playing = False
            self.floating_player.update_display(self.current_playing_song, False)
            self.floating_player.stop_timer()  # Stop timer tapi JANGAN reset elapsed_seconds
            
            # PAUSE AUDIO
            if PYGAME_AVAILABLE and not self.pygame_error:
                try:
                    pygame.mixer.music.pause()
                except:
                    pass
        else:
            # RESUME atau START
            if not self.current_playing_song and self.current_playlist and self.current_playlist.head:
                first_song_id = self.current_playlist.head.song_id
                self.current_playing_song = self.library.id_map.get(first_song_id)
                self.playback_context = "playlist"
                if self.shuffle_enabled:
                    self.current_index_in_shuffle = 0
                # FIX BUG #1: Set current_play pointer
                self.current_playlist.current_play = self.current_playlist.head
            
            if self.current_playing_song:
                self.is_playing = True
                self._show_floating_player()
                self.floating_player.update_display(self.current_playing_song, True)
                
                # FIX BUG #6: Use resume_timer untuk melanjutkan dari posisi terakhir
                self.floating_player.resume_timer()
                
                # UNPAUSE AUDIO
                if PYGAME_AVAILABLE and not self.pygame_error:
                    try:
                        pygame.mixer.music.unpause()
                        # Jika music tidak playing (stopped), reload dan play
                        if not pygame.mixer.music.get_busy() and self.current_playing_song.file_path:
                            pygame.mixer.music.load(self.current_playing_song.file_path)
                            pygame.mixer.music.play()
                    except:
                        pass
            else:
                messagebox.showwarning("Peringatan", "Tidak ada lagu yang dipilih.")

    def _toggle_shuffle(self):
        """Toggle shuffle mode - Modified to allow setting even if context is not playlist"""
        # FIX: Allow if playlist exists/selected
        if not self.current_playlist or not self.current_playlist.head:
             messagebox.showwarning("Peringatan", "Playlist kosong atau tidak dipilih!")
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
        """Cycle repeat mode - Modified to allow setting even if context is not playlist"""
        # FIX: Allow if playlist exists/selected
        if not self.current_playlist:
             messagebox.showwarning("Peringatan", "Pilih playlist terlebih dahulu!")
             return
            
        self.repeat_mode = "playlist" if self.repeat_mode == "none" else "none"
        
        # FIX: Update Button Text
        text = f"🔁 Repeat: {self.repeat_mode.upper()}" if self.repeat_mode != "none" else "🔁 Repeat: OFF"
        try: 
            if hasattr(self, 'btn_repeat') and self.btn_repeat:
                self.btn_repeat.config(text=text)
        except: pass
        
        try:
            self.floating_player.update_display(self.current_playing_song, self.is_playing)
        except: pass

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
        
        # PRIORITAS 3: Jika dari LIBRARY SEQUENTIAL (pure urutan)
        if self.playback_context == "library_sequential":
            self._next_song_sequential()
            return
        
        # PRIORITAS 4: Jika dari LIBRARY SIMILAR (dengan kemiripan)
        if self.playback_context == "library_similar":
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



    
    def _next_song_sequential(self):
        """Next song dalam mode sequential - PURE URUTAN LIBRARY"""
        try:
            all_songs = self.library.get_all_songs()
            if not all_songs:
                print("DEBUG: Library kosong")
                try:
                    self._show_toast("⚠️ Library kosong!")
                except:
                    pass
                return
            
            # Cari index lagu sekarang
            if self.current_playing_song:
                try:
                    current_idx = next(i for i, s in enumerate(all_songs) if s.id == self.current_playing_song.id)
                except StopIteration:
                    current_idx = self.current_library_index if hasattr(self, 'current_library_index') else 0
            else:
                current_idx = self.current_library_index if hasattr(self, 'current_library_index') else 0
            
            # Next index (urut)
            next_idx = (current_idx + 1) % len(all_songs)
            next_song = all_songs[next_idx]
            
            # Update index
            self.current_library_index = next_idx
            
            # Play lagu berikutnya dengan context yang sama
            print(f"DEBUG: Sequential next: {next_song.title} (index {next_idx})")
            self._start_playing_song(next_song, "library_sequential")
            
            try:
                self._show_toast(f"⏭️ Berikutnya: {next_song.title}")
            except:
                pass
                
        except Exception as e:
            print(f"DEBUG: Sequential next error: {e}")
            import traceback
            traceback.print_exc()


    def _play_similar_song(self):
        """Play lagu yang mirip dengan lagu sekarang - Prioritas: Artis > Genre > Pesan (NO LOOPING)"""
        try:
            if not self.current_playing_song:
                return

            all_songs = self.library.get_all_songs()
            
            # Validasi: library kosong
            if not all_songs:
                try:
                    self._show_toast("⚠️ Library kosong!")
                except:
                    pass
                return

            # FIX: Prevent Looping - Exclude played songs
            played_ids = set()
            try:
                if hasattr(self, 'songs_played'):
                    for s in self.songs_played:
                        played_ids.add(s.id)
            except:
                pass
            
            # Always exclude current song (redundant but safe)
            played_ids.add(self.current_playing_song.id)

            # Filter candidates: Exclude songs that have been played
            candidates = [s for s in all_songs if s.id not in played_ids]
            
            # Check if we ran out of songs entirely (optional, but good for debug)
            # if not candidates:
            #    print("DEBUG: All songs played.")

            # PRIORITAS 1: Artis Sama (Case Insensitive)
            same_artist = [s for s in candidates if s.artist.lower().strip() == self.current_playing_song.artist.lower().strip()]
            if same_artist:
                next_song = random.choice(same_artist)
                print(f"DEBUG: ✓ Memutar lagu dengan artis sama (No Loop): {next_song.artist}")
                try:
                    self._show_toast(f"🎵 Artis sama: {next_song.artist}")
                except:
                    pass
                self._start_playing_song(next_song, "library_similar")
                return

            # PRIORITAS 2: Genre Sama (Case Insensitive)
            same_genre = [s for s in candidates if s.genre.lower().strip() == self.current_playing_song.genre.lower().strip()]
            if same_genre:
                next_song = random.choice(same_genre)
                print(f"DEBUG: ✓ Memutar lagu dengan genre sama (No Loop): {next_song.genre}")
                try:
                    self._show_toast(f"🎼 Genre sama: {next_song.genre}")
                except:
                    pass
                self._start_playing_song(next_song, "library_similar")
                return
                
            # TIDAK ADA LAGU MIRIP: Tampilkan pesan dan STOP
            print(f"DEBUG: ⚠️ Tidak ada lagu mirip lagi.")
            try:
                self._show_toast(f"⚠️ Tidak ada lagu yang mirip sesuai Artis/Genre.")
            except:
                pass
            
            # STOP PLAYBACK - Reached end of similar chain
            self.is_playing = False
            self.floating_player.stop_timer()
            try:
                if PYGAME_AVAILABLE and not self.pygame_error:
                     pygame.mixer.music.stop()
            except:
                pass
            
            self.floating_player.update_display(self.current_playing_song, False)
            return
                    
        except Exception as e:
            print(f"DEBUG: Play similar error: {e}")
            import traceback
            traceback.print_exc()
            try:
                self._show_toast("❌ Terjadi kesalahan saat mencari lagu mirip")
            except:
                pass


    def _prev_song(self):
        """Previous song"""
        if not self.current_playing_song:
            return
        
        if self.playback_context == "playlist":
            self._prev_song_from_playlist()
        elif self.playback_context == "library_sequential":
            self._prev_song_sequential()
        elif self.playback_context == "library_similar":
            self._prev_song_from_library()

    
    def _prev_song_from_playlist(self):
        """Previous song dalam mode playlist - FIX BUG #1: Gunakan doubly linked list"""
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
            # FIX BUG #1: Use Doubly Linked List untuk prev
            if self.current_playlist and self.current_playlist.current_play:
                prev_node = self.current_playlist.current_play.prev
                
                if prev_node:
                    prev_song = self.library.id_map.get(prev_node.song_id)
                    if prev_song:
                        # FIX BUG #1: Update current_play pointer
                        self.current_playlist.current_play = prev_node
                        self._start_playing_song(prev_song, "playlist")
                        return
            
            # Jika tidak ada prev, tidak melakukan apa-apa
    
    
    def _prev_song_from_library(self):
        """Previous song dalam mode library - Cari LAGU MIRIP (Sama dengan Next)"""
        # Requirement: "Next/prev akan memutar lagu yang mirip"
        self._play_similar_song()
    
    def _prev_song_sequential(self):
        """Previous song dalam mode sequential - PURE URUTAN LIBRARY"""
        try:
            all_songs = self.library.get_all_songs()
            if not all_songs:
                print("DEBUG: Library kosong")
                try:
                    self._show_toast("⚠️ Library kosong!")
                except:
                    pass
                return
            
            # Cari index lagu sekarang
            if self.current_playing_song:
                try:
                    current_idx = next(i for i, s in enumerate(all_songs) if s.id == self.current_playing_song.id)
                except StopIteration:
                    current_idx = self.current_library_index if hasattr(self, 'current_library_index') else 0
            else:
                current_idx = self.current_library_index if hasattr(self, 'current_library_index') else 0
            
            # Previous index (urut, dengan wrap around)
            prev_idx = (current_idx - 1) % len(all_songs)
            prev_song = all_songs[prev_idx]
            
            # Update index
            self.current_library_index = prev_idx
            
            # Play lagu sebelumnya dengan context yang sama
            print(f"DEBUG: Sequential prev: {prev_song.title} (index {prev_idx})")
            self._start_playing_song(prev_song, "library_sequential")
            
            try:
                self._show_toast(f"⏮️ Sebelumnya: {prev_song.title}")
            except:
                pass
                
        except Exception as e:
            print(f"DEBUG: Sequential prev error: {e}")
            import traceback
            traceback.print_exc()



if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayerApp(root)
    root.mainloop()