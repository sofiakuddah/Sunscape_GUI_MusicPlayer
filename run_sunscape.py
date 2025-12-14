"""
SUNSCAPE Music Player Launcher
Jalankan file ini untuk membuka aplikasi SUNSCAPE
"""
import sys
import os

# Tambahkan parent directory ke Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import dan jalankan aplikasi
import tkinter as tk
from main.gui.app import MusicPlayerApp

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayerApp(root)
    root.mainloop()
