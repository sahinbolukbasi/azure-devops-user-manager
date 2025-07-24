#!/usr/bin/env python3
"""
Azure DevOps User Assignment Tool
Excel tabanlı kullanıcı atama aracı
"""

import tkinter as tk
from gui.main_window import MainWindow

def main():
    """Ana uygulama başlangıcı"""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()