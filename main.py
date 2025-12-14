import tkinter as tk
from main.gui.app import MusicPlayerApp

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayerApp(root)
    root.mainloop()